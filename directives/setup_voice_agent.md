# Directive: Set Up Voice Agent

## Goal
Bring the voice agent from clean clone → running locally with a public webhook ready to accept a Twilio test call.

## Inputs
- `.env` populated from `.env.example`
- Public HTTPS tunnel (ngrok, Cloudflare Tunnel, or deployed host) for Twilio webhooks

## Tools to use (in order)
1. `execution/setup_voice_agent.py` — verifies env, creates `.tmp/`, prints next steps
2. `uvicorn execution.twilio_websocket_server:app` — starts the WebSocket + TwiML server
3. `execution/call_initiator.py --to <number>` — places an outbound test call

## Outputs
- Running server on `SERVER_PORT`
- `PUBLIC_URL/twiml` returns valid TwiML with `<Connect><Stream>` pointing at `PUBLIC_URL/ws`
- A live test call connects and is logged to `.tmp/calls/<call_sid>.json`

## Edge cases
- Twilio drops the stream after ~30s of silence — keepalive `mark` messages handled in [twilio_stream.md](twilio_stream.md)
- Local-only testing requires a public tunnel; Twilio will not connect to localhost
- mulaw 8kHz mono is the only inbound codec — do not assume PCM
