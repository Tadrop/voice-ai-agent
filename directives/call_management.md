# Directive: Call Management

## Goal
Place, track, and record outbound calls; persist transcripts and outcomes.

## Inputs
- Target phone number (E.164)
- Optional campaign / script identifier
- Twilio credentials from `.env`

## Tools
- `execution/call_initiator.py` — places outbound calls via Twilio REST
- `execution/transcript_storage.py` — persists per-call JSON to `.tmp/calls/` (or DB if `DATABASE_URL` set)

## Outputs
- Twilio call SID
- `.tmp/calls/<call_sid>.json` containing: timestamps, transcript turns, outcome, duration
- Optional row in `calls` table (if DB configured)

## Edge cases
- **Compliance**: respect Do-Not-Call lists and per-region calling-hour rules — caller must supply this filter, agent does not infer it.
- **Webhook verification**: validate Twilio signatures on `/twiml` to reject spoofed requests.
- **Retries**: on `busy`/`no-answer`, retry policy must be explicit in the campaign config — never silently retry.
- **PII**: transcripts may contain PII; redact in logs, store only in encrypted destination for production.
