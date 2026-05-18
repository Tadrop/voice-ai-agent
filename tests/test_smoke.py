"""Smoke tests — verify modules import and basic endpoints respond."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent


def test_directives_exist():
    # deployment.md is intentionally gitignored (delivered out-of-band)
    expected = [
        "setup_voice_agent.md",
        "twilio_stream.md",
        "stt_pipeline.md",
        "llm_orchestrator.md",
        "tts_pipeline.md",
        "call_management.md",
        "generate_workflow_diagram.md",
    ]
    for name in expected:
        assert (ROOT / "directives" / name).is_file(), f"missing directive: {name}"


def test_execution_scripts_importable():
    from execution import (  # noqa: F401
        call_initiator,
        generate_workflow_diagram,
        llm_client,
        setup_voice_agent,
        stt_client,
        transcript_storage,
        tts_client,
        twilio_websocket_server,
    )


def test_llm_sentence_splitter_regex():
    from execution.llm_client import _SENTENCE_END

    assert _SENTENCE_END.search("Hello world. ")
    assert _SENTENCE_END.search("Wait!\n")
    assert _SENTENCE_END.search("Why? Yes.")
    assert not _SENTENCE_END.search("no terminator yet")


def test_stt_client_url_includes_mulaw_8k():
    import os
    os.environ.setdefault("DEEPGRAM_API_KEY", "test")
    from execution.stt_client import DeepgramStream

    stt = DeepgramStream()
    assert "encoding=mulaw" in stt._url
    assert "sample_rate=8000" in stt._url


def test_tts_client_url_outputs_ulaw_8000():
    import os
    os.environ.setdefault("ELEVENLABS_API_KEY", "test")
    os.environ.setdefault("ELEVENLABS_VOICE_ID", "test")
    from execution.tts_client import ElevenLabsStream

    tts = ElevenLabsStream()
    assert "output_format=ulaw_8000" in tts._url
    assert "stream-input" in tts._url


def test_setup_detects_missing_env(monkeypatch):
    from execution import setup_voice_agent

    for key in setup_voice_agent.REQUIRED_KEYS:
        monkeypatch.delenv(key, raising=False)
    missing = setup_voice_agent.check_env()
    assert set(missing) == set(setup_voice_agent.REQUIRED_KEYS)


def test_healthz_and_twiml():
    from execution.twilio_websocket_server import app

    client = TestClient(app)

    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

    r = client.post("/twiml")
    assert r.status_code == 200
    assert "<Stream" in r.text
    assert "wss://" in r.text or "ws://" in r.text


def test_diagram_generation_writes_sources(tmp_path, monkeypatch):
    from execution import generate_workflow_diagram as g

    monkeypatch.setattr(g, "OUT", tmp_path)
    g.main()
    assert (tmp_path / "workflow_diagram.mmd").is_file()
    assert (tmp_path / "workflow_diagram.dot").is_file()


def test_gitignore_protects_secrets():
    gi = (ROOT / ".gitignore").read_text()
    for must_ignore in [".env", "DEPLOYMENT.md", "credentials.json", "token.json", ".tmp/"]:
        assert must_ignore in gi, f".gitignore missing entry: {must_ignore}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
