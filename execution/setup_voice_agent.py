"""Verify environment and scaffold runtime directories.

Run: python execution/setup_voice_agent.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_KEYS = [
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_PHONE_NUMBER",
    "OPENAI_API_KEY",
    "DEEPGRAM_API_KEY",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_VOICE_ID",
    "PUBLIC_URL",
]


def ensure_dirs() -> None:
    for sub in (".tmp", ".tmp/calls", ".tmp/audio"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)


def check_env() -> list[str]:
    if load_dotenv is not None:
        load_dotenv(ROOT / ".env")
    return [k for k in REQUIRED_KEYS if not os.getenv(k)]


def main() -> int:
    ensure_dirs()
    missing = check_env()
    if missing:
        print("Missing required env vars:", ", ".join(missing))
        print("Copy .env.example to .env and fill them in.")
        return 1
    print("Env OK. Directories ready.")
    print("Next: uvicorn execution.twilio_websocket_server:app --host 0.0.0.0 --port", os.getenv("SERVER_PORT", "8000"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
