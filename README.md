# Real-Time Voice Call AI Agent

Outbound conversational voice agent: Twilio Media Streams → STT → LLM → TTS, back-and-forth in real time.

## Architecture

3 layers — **Directives** (`directives/`, what to do) → **Orchestration** (the agent, decision-making) → **Execution** (`execution/`, deterministic scripts). See [CLAUDE.md](CLAUDE.md).

```
Caller → Twilio → WebSocket → STT → LLM → TTS → WebSocket → Twilio → Caller
```

## Quick start

```bash
cp .env.example .env          # fill in keys
pip install -r requirements.txt
python execution/setup_voice_agent.py
uvicorn execution.twilio_websocket_server:app --host 0.0.0.0 --port 8000
```

Configure your Twilio number's webhook to `https://<your-public-host>/twiml` and trigger a test call:

```bash
python execution/call_initiator.py --to +15551234567
```

## Layout

- [directives/](directives/) — SOPs the agent reads before doing work
- [execution/](execution/) — Python tools the agent runs
- [.tmp/](.tmp/) — intermediates (gitignored, regenerable)
- `.env` — secrets (gitignored)
- `DEPLOYMENT.md` — client-specific deployment runbook (gitignored)

## CI

GitHub Actions runs `ruff` + `pytest` on push/PR. See [.github/workflows/ci.yml](.github/workflows/ci.yml).
