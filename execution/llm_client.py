"""OpenAI streaming chat completions, yielded sentence-by-sentence for low-latency TTS."""
from __future__ import annotations

import os
import re
from typing import AsyncIterator

from openai import AsyncOpenAI

DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
DEFAULT_SYSTEM_PROMPT = (
    "You are a friendly, concise voice agent on a phone call. "
    "Speak naturally, keep replies under two short sentences when possible, "
    "and never use markdown or special characters — your text becomes audio."
)

_SENTENCE_END = re.compile(r"([.!?]+\s|\n+)")


async def stream_reply(messages: list[dict], model: str = DEFAULT_MODEL) -> AsyncIterator[str]:
    client = AsyncOpenAI()
    buffer = ""
    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        temperature=0.7,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if not delta:
            continue
        buffer += delta
        while True:
            m = _SENTENCE_END.search(buffer)
            if not m:
                break
            sentence = buffer[: m.end()].strip()
            buffer = buffer[m.end():]
            if sentence:
                yield sentence
    tail = buffer.strip()
    if tail:
        yield tail
