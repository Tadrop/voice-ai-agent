"""FastAPI server: TwiML endpoint + Twilio Media Stream WebSocket bridge.

Wires Twilio <-> Deepgram STT <-> OpenAI LLM <-> ElevenLabs TTS with barge-in and keepalives.
Run: uvicorn execution.twilio_websocket_server:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse

from execution.llm_client import DEFAULT_SYSTEM_PROMPT, stream_reply
from execution.stt_client import DeepgramStream
from execution.transcript_storage import save_transcript
from execution.tts_client import ElevenLabsStream

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PUBLIC_URL = os.getenv("PUBLIC_URL", "https://example.test")
GREETING = os.getenv("AGENT_GREETING", "Hi there. Thanks for taking my call. How are you today?")
SYSTEM_PROMPT = os.getenv("AGENT_SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT)
KEEPALIVE_S = 10.0

ROOT = Path(__file__).resolve().parent.parent
CALLS_DIR = ROOT / ".tmp" / "calls"
CALLS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Voice AI Agent")


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.api_route("/twiml", methods=["GET", "POST"])
async def twiml(_request: Request) -> PlainTextResponse:
    ws_url = PUBLIC_URL.replace("https://", "wss://").replace("http://", "ws://") + "/ws"
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="{ws_url}" />
  </Connect>
</Response>"""
    return PlainTextResponse(body, media_type="application/xml")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _once(text: str) -> AsyncIterator[str]:
    yield text


class CallSession:
    def __init__(self, twilio_ws: WebSocket) -> None:
        self.twilio_ws = twilio_ws
        self.stream_sid: str | None = None
        self.call_sid: str | None = None
        self.started_at = datetime.now(timezone.utc)
        self.history: list[dict] = []
        self.transcript: list[dict] = []
        self.speech_task: asyncio.Task | None = None
        self.stt: DeepgramStream | None = None
        self.closed = asyncio.Event()

    async def send_media(self, payload_b64: str) -> None:
        await self.twilio_ws.send_text(json.dumps({
            "event": "media",
            "streamSid": self.stream_sid,
            "media": {"payload": payload_b64},
        }))

    async def send_clear(self) -> None:
        await self.twilio_ws.send_text(json.dumps({
            "event": "clear",
            "streamSid": self.stream_sid,
        }))

    async def send_mark(self, name: str | None = None) -> None:
        await self.twilio_ws.send_text(json.dumps({
            "event": "mark",
            "streamSid": self.stream_sid,
            "mark": {"name": name or f"k-{uuid4().hex[:6]}"},
        }))


async def _pump_tts_to_twilio(session: CallSession, tts: ElevenLabsStream) -> None:
    with suppress(Exception):
        async for audio_b64 in tts.audio_chunks():
            await session.send_media(audio_b64)


async def _speak(session: CallSession, sentences: AsyncIterator[str]) -> str:
    spoken: list[str] = []
    async with ElevenLabsStream() as tts:
        consumer = asyncio.create_task(_pump_tts_to_twilio(session, tts))
        try:
            async for sentence in sentences:
                spoken.append(sentence)
                await tts.send_text(sentence)
            await tts.close_input()
            await consumer
        finally:
            consumer.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await consumer
    return " ".join(spoken).strip()


async def speak_greeting(session: CallSession) -> None:
    spoken = ""
    try:
        spoken = await _speak(session, _once(GREETING))
    except asyncio.CancelledError:
        raise
    except Exception as e:
        print(f"greeting failed: {e}")
    finally:
        text = spoken or GREETING
        session.history.append({"role": "assistant", "content": text})
        session.transcript.append({"role": "assistant", "text": text, "ts": _now_iso()})


async def respond(session: CallSession) -> None:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *session.history]
    spoken = ""
    try:
        spoken = await _speak(session, stream_reply(messages))
    except asyncio.CancelledError:
        raise
    except Exception as e:
        print(f"respond failed: {e}")
    finally:
        if spoken:
            session.history.append({"role": "assistant", "content": spoken})
            session.transcript.append({"role": "assistant", "text": spoken, "ts": _now_iso()})


async def twilio_inbound_pump(session: CallSession) -> None:
    while True:
        try:
            raw = await session.twilio_ws.receive_text()
        except WebSocketDisconnect:
            session.closed.set()
            return
        data = json.loads(raw)
        event = data.get("event")
        if event == "start":
            session.stream_sid = data["start"]["streamSid"]
            session.call_sid = data["start"]["callSid"]
            session.speech_task = asyncio.create_task(speak_greeting(session))
        elif event == "media":
            payload = data.get("media", {}).get("payload")
            if session.stt is not None and payload:
                with suppress(Exception):
                    await session.stt.send_audio(base64.b64decode(payload))
        elif event == "stop":
            session.closed.set()
            return


async def stt_consumer(session: CallSession) -> None:
    assert session.stt is not None
    async for event in session.stt.events():
        etype = event["type"]
        if etype == "speech_started":
            if session.speech_task and not session.speech_task.done():
                session.speech_task.cancel()
                with suppress(Exception):
                    await session.send_clear()
        elif etype == "transcript" and event["is_final"] and event["speech_final"]:
            text = event["text"].strip()
            if not text:
                continue
            session.history.append({"role": "user", "content": text})
            session.transcript.append({"role": "user", "text": text, "ts": _now_iso()})
            if session.speech_task and not session.speech_task.done():
                session.speech_task.cancel()
                with suppress(asyncio.CancelledError, Exception):
                    await session.speech_task
                with suppress(Exception):
                    await session.send_clear()
            session.speech_task = asyncio.create_task(respond(session))


async def keepalive_pump(session: CallSession) -> None:
    while not session.closed.is_set():
        try:
            await asyncio.wait_for(session.closed.wait(), timeout=KEEPALIVE_S)
            return
        except asyncio.TimeoutError:
            if session.stream_sid:
                with suppress(Exception):
                    await session.send_mark("keepalive")
            if session.stt is not None:
                with suppress(Exception):
                    await session.stt.keepalive()


@app.websocket("/ws")
async def media_stream(ws: WebSocket) -> None:
    await ws.accept()
    session = CallSession(twilio_ws=ws)
    try:
        async with DeepgramStream() as stt:
            session.stt = stt
            tasks = [
                asyncio.create_task(twilio_inbound_pump(session)),
                asyncio.create_task(stt_consumer(session)),
                asyncio.create_task(keepalive_pump(session)),
            ]
            _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for t in pending:
                t.cancel()
            for t in pending:
                with suppress(asyncio.CancelledError, Exception):
                    await t
            if session.speech_task and not session.speech_task.done():
                session.speech_task.cancel()
                with suppress(asyncio.CancelledError, Exception):
                    await session.speech_task
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"/ws error: {e}")
    finally:
        if session.call_sid and session.transcript:
            duration = (datetime.now(timezone.utc) - session.started_at).total_seconds()
            with suppress(Exception):
                save_transcript(
                    call_sid=session.call_sid,
                    turns=session.transcript,
                    outcome="completed",
                    duration_s=duration,
                )
