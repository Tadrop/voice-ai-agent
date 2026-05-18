# Directive: Speech-to-Text Pipeline

## Goal
Convert inbound caller audio into low-latency text events the LLM can act on.

## Inputs
- mulaw 8kHz audio frames from `twilio_stream`
- `DEEPGRAM_API_KEY` in `.env`

## Tools
- Deepgram streaming WS client (preferred). Fallback: AssemblyAI realtime.
- Embedded inside `execution/twilio_websocket_server.py` as the STT task.

## Outputs
- `partial` transcript events (for interruption/barge-in detection)
- `final` transcript events (committed to LLM as a user turn)
- `speech_started` / `utterance_end` events

## Edge cases
- **Endpointing**: use `endpointing=300` ms; lower causes premature cut-off, higher adds lag.
- **Filler-only finals** ("uh", "um") — drop before sending to LLM.
- **Reconnect**: STT WS can drop independently of Twilio. Re-establish without tearing down the Twilio stream.
- **Language**: default `en-US`. Override per-call via call metadata if needed.
