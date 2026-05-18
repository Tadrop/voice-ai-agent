# Directive: Deployment

## Goal
Run the WebSocket server on a public, low-latency host with HTTPS, with Twilio pointed at it.

## Inputs
- Docker installed (or target PaaS: Fly.io / Modal / Render / Railway)
- `.env` with production keys
- Domain or provider-issued HTTPS URL

## Tools
- `Dockerfile` (build with `docker build -t voice-agent .`)
- `execution/twilio_websocket_server.py` (uvicorn entrypoint)
- Cloud-provider CLI of choice

## Outputs
- Public HTTPS endpoint serving `/twiml` (HTTPS) and `/ws` (WSS)
- Twilio Phone Number's Voice Configuration → `A CALL COMES IN` webhook = `https://<host>/twiml`
- Health endpoint `/healthz` returning 200

## Edge cases
- **Region**: deploy in the same region as the Twilio media region you select (lower RTT).
- **Cold starts**: serverless platforms with cold-start > 1s will drop the first call. Use a warm instance.
- **Concurrency**: each concurrent call = 1 WS + STT WS + TTS WS. Size accordingly.
- **Secrets**: never bake `.env` into the image. Use the provider's secret manager.

## Client-facing runbook
The full client-specific deployment steps (provider, domain, secret values, post-deploy verification) live in `DEPLOYMENT.md` at the repo root. **`DEPLOYMENT.md` is gitignored** — it contains client/infra-specific information and is delivered to the client out-of-band.
