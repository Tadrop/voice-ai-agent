# Directive: Text-to-Speech Pipeline

## Goal
Stream assistant audio back to the caller with minimal time-to-first-audio.

## Inputs
- Streamed text deltas from `llm_orchestrator`
- `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`

## Tools
- ElevenLabs WebSocket streaming TTS (`/v1/text-to-speech/{voice}/stream-input`)
- Audio resampler to convert ElevenLabs output to mulaw 8kHz

## Outputs
- Outbound `media` frames sent over Twilio WS
- Per-sentence `mark` events so we can detect playback completion and barge-in

## Edge cases
- **Time-to-first-audio**: aim < 400ms. Pre-warm the WS at call start.
- **Barge-in**: on `speech_started` from STT, send `clear` to Twilio and abort the current TTS WS stream.
- **Pronunciation**: pass SSML where supported (numbers, currencies, dates).
- **Rate limits**: ElevenLabs concurrency caps per plan — surface clear errors.
