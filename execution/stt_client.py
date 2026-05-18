"""Deepgram streaming STT over WebSocket. Accepts mulaw 8k, emits transcript / VAD events."""
from __future__ import annotations

import json
import os
from typing import AsyncIterator
from urllib.parse import urlencode

import websockets

_DEFAULTS = {
    "encoding": "mulaw",
    "sample_rate": "8000",
    "channels": "1",
    "interim_results": "true",
    "endpointing": "300",
    "vad_events": "true",
    "model": "nova-2-phonecall",
    "punctuate": "true",
    "smart_format": "true",
}


class DeepgramStream:
    def __init__(self, api_key: str | None = None, **params: str) -> None:
        self.api_key = api_key or os.environ["DEEPGRAM_API_KEY"]
        self.params = {**_DEFAULTS, **params}
        self._url = f"wss://api.deepgram.com/v1/listen?{urlencode(self.params)}"
        self._ws = None

    async def __aenter__(self) -> "DeepgramStream":
        headers = {"Authorization": f"Token {self.api_key}"}
        try:
            self._ws = await websockets.connect(self._url, additional_headers=headers)
        except TypeError:
            self._ws = await websockets.connect(self._url, extra_headers=headers)
        return self

    async def __aexit__(self, *exc) -> None:
        if self._ws is None:
            return
        try:
            await self._ws.send(json.dumps({"type": "CloseStream"}))
        except Exception:
            pass
        await self._ws.close()

    async def send_audio(self, mulaw_bytes: bytes) -> None:
        await self._ws.send(mulaw_bytes)

    async def keepalive(self) -> None:
        await self._ws.send(json.dumps({"type": "KeepAlive"}))

    async def events(self) -> AsyncIterator[dict]:
        async for raw in self._ws:
            if isinstance(raw, bytes):
                continue
            msg = json.loads(raw)
            mtype = msg.get("type")
            if mtype == "Results":
                alt = msg.get("channel", {}).get("alternatives", [{}])[0]
                text = alt.get("transcript", "")
                if not text:
                    continue
                yield {
                    "type": "transcript",
                    "text": text,
                    "is_final": bool(msg.get("is_final")),
                    "speech_final": bool(msg.get("speech_final")),
                }
            elif mtype == "SpeechStarted":
                yield {"type": "speech_started"}
            elif mtype == "UtteranceEnd":
                yield {"type": "utterance_end"}
