"""ElevenLabs streaming TTS over WebSocket. Outputs base64 mulaw 8k for direct Twilio forwarding."""
from __future__ import annotations

import json
import os
from typing import AsyncIterator

import websockets

DEFAULT_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5")


class ElevenLabsStream:
    def __init__(
        self,
        voice_id: str | None = None,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
    ) -> None:
        self.api_key = api_key or os.environ["ELEVENLABS_API_KEY"]
        self.voice_id = voice_id or os.environ["ELEVENLABS_VOICE_ID"]
        self.model = model
        self._url = (
            f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input"
            f"?model_id={self.model}&output_format=ulaw_8000"
        )
        self._ws = None

    async def __aenter__(self) -> "ElevenLabsStream":
        self._ws = await websockets.connect(self._url)
        await self._ws.send(json.dumps({
            "text": " ",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
            "generation_config": {"chunk_length_schedule": [120, 160, 250, 290]},
            "xi_api_key": self.api_key,
        }))
        return self

    async def __aexit__(self, *exc) -> None:
        if self._ws is None:
            return
        try:
            await self._ws.close()
        except Exception:
            pass

    async def send_text(self, text: str) -> None:
        await self._ws.send(json.dumps({"text": text + " ", "try_trigger_generation": True}))

    async def close_input(self) -> None:
        await self._ws.send(json.dumps({"text": ""}))

    async def audio_chunks(self) -> AsyncIterator[str]:
        async for raw in self._ws:
            if isinstance(raw, bytes):
                continue
            msg = json.loads(raw)
            if msg.get("audio"):
                yield msg["audio"]
            if msg.get("isFinal"):
                break
