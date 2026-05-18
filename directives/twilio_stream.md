# Directive: Twilio Media Stream

## Goal
Maintain a duplex audio bridge between Twilio and the agent over WebSockets.

## Inputs
- Twilio WebSocket connection at `/ws`
- Incoming JSON frames: `connected`, `start`, `media`, `mark`, `stop`

## Tools
- `execution/twilio_websocket_server.py` — FastAPI app with `/twiml` and `/ws` endpoints

## Outputs
- Inbound mulaw 8kHz audio decoded → forwarded to STT
- Outbound TTS audio re-encoded to mulaw 8kHz → framed back to Twilio as `media` events
- `mark` events used as keepalive every ~10s and to confirm playback boundaries

## Edge cases
- **Codec**: Twilio only sends `audio/x-mulaw;rate=8000`. Re-sample TTS output (usually 16k/24k PCM) to mulaw 8k before sending.
- **30s silence drop**: Send a benign `mark` event during silence to keep the stream alive.
- **Barge-in**: When STT emits a `speech_started` event while TTS is mid-playback, send `clear` to Twilio to flush queued audio.
- **Sequencing**: Twilio requires monotonically increasing `sequenceNumber` on outbound `media` frames.
