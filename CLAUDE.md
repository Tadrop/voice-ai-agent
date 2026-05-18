# Agent Instructions

> This file is mirrored across CLAUDE.md, AGENTS.md, and GEMINI.md so the same instructions load in any AI environment.

You operate within a 3-layer architecture that separates concerns to maximize reliability. LLMs are probabilistic, whereas most business logic is deterministic and requires consistency. This system fixes that mismatch.

## Project: Real-Time Voice Call AI Agent

A conversational AI system that makes outbound phone calls, speaks naturally with prospects, and handles real-time back-and-forth dialogue. The agent uses an LLM for intelligence, STT/TTS for voice processing, and Twilio for phone integration.

## The 3-Layer Architecture

**Layer 1: Directive (What to do)**
- SOPs written in Markdown, live in `directives/`
- Define goals, inputs, tools/scripts to use, outputs, and edge cases
- Natural language instructions, like you'd give a mid-level engineer

**Layer 2: Orchestration (Decision making)**
- This is you. Your job: intelligent routing.
- Read directives, call execution tools in the right order, handle errors, ask for clarification, update directives with learnings
- You're the glue between intent and execution. E.g., you don't try wiring WebSockets manually — you read `directives/setup_twilio_stream.md` and run `execution/setup_twilio_stream.py`

**Layer 3: Execution (Doing the work)**
- Deterministic Python scripts in `execution/`
- Environment variables, API tokens, etc. are stored in `.env`
- Handle API calls, audio streaming, data processing, database interactions
- Reliable, testable, fast. Use scripts instead of manual work.

**Why this works:** if you do everything yourself, errors compound. 90% accuracy per step = 59% success over 5 steps. Push complexity into deterministic code. That way you focus on decision-making.

## Operating Principles

**1. Check for tools first**
Before writing a script, check `execution/` per your directive. Only create new scripts if none exist.

**2. Self-anneal when things break**
- Read error message and stack trace
- Fix the script and test it again (unless it uses paid tokens/credits/etc — in which case you check w/ user first)
- Update the directive with what you learned (API limits, timing, audio codec edge cases, latency issues)
- Example: Twilio drops the stream after 30s silence → you then look into keepalive/ping logic → rewrite script → test → update directive.

**3. Update directives as you learn**
Directives are living documents. When you discover API constraints, better approaches, common errors, or timing expectations — update the directive. But don't create or overwrite directives without asking unless explicitly told to. Directives are your instruction set and must be preserved (and improved upon over time, not extemporaneously used and then discarded).

## Self-annealing loop

Errors are learning opportunities. When something breaks:
1. Fix it
2. Update the tool
3. Test tool, make sure it works
4. Update directive to include new flow
5. System is now stronger

## File Organization

**Deliverables vs Intermediates:**
- **Deliverables**: Working deployed voice agent, call logs dashboard, API endpoints
- **Intermediates**: Temporary files needed during processing

**Directory structure:**
- `.tmp/` - All intermediate files (audio chunks, temp transcripts, test recordings). Never commit, always regenerated.
- `execution/` - Python scripts (the deterministic tools)
- `directives/` - SOPs in Markdown (the instruction set)
- `.env` - Environment variables and API keys (Twilio, OpenAI, Deepgram, ElevenLabs)
- `credentials.json`, `token.json` - OAuth credentials if needed (in `.gitignore`)

**Key principle:** Local files are only for processing. Deliverables are deployed services. Everything in `.tmp/` can be deleted and regenerated.

## Core Components

### 1. Twilio Stream Integration (`directives/twilio_stream.md`)
- WebSocket connection to Twilio Media Streams
- Receives inbound audio (mulaw/PCM), sends outbound audio
- Handles call events: `start`, `media`, `stop`, `mark`

### 2. Speech-to-Text (`directives/stt_pipeline.md`)
- Real-time streaming STT via Deepgram or AssemblyAI
- Converts caller audio to text chunks for the LLM
- Handles speaker diarization if needed

### 3. LLM Orchestrator (`directives/llm_orchestrator.md`)
- OpenAI GPT-4 / Claude API for conversation intelligence
- Maintains conversation context and business logic
- Generates responses based on caller input and system prompts

### 4. Text-to-Speech (`directives/tts_pipeline.md`)
- Real-time TTS via ElevenLabs or similar
- Streams generated audio back to Twilio with minimal latency
- Supports voice cloning / custom voice profiles

### 5. Call Management (`directives/call_management.md`)
- Initiates outbound calls via Twilio REST API
- Tracks call state, duration, outcomes
- Stores transcripts and summaries in database

### 6. Deployment (`directives/deployment.md`)
- FastAPI/Flask server for WebSocket handling
- Docker containerization
- Cloud deployment (AWS/GCP/Modal)

## Webhook & Streaming Architecture

**When user says "set up a voice call agent" or "deploy the agent":**
1. Read `directives/setup_voice_agent.md` for complete instructions
2. Verify `.env` has all required keys (Twilio, OpenAI, Deepgram, ElevenLabs)
3. Run `execution/setup_voice_agent.py` to scaffold the project
4. Deploy the WebSocket server
5. Configure Twilio webhook URL to point to your server
6. Test with a live call

**Key files:**
- `execution/setup_voice_agent.py` - Project scaffolding and dependency install
- `execution/twilio_websocket_server.py` - Main WebSocket server handling audio streams
- `execution/call_initiator.py` - Script to trigger outbound calls
- `execution/transcript_storage.py` - Save call transcripts and summaries
- `directives/setup_voice_agent.md` - Complete setup guide

**Audio pipeline flow:**
```
Caller → Twilio → WebSocket → STT → LLM → TTS → WebSocket → Twilio → Caller
```

## API Keys & Environment

Required in `.env`:
- `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_PHONE_NUMBER`
- `OPENAI_API_KEY`
- `DEEPGRAM_API_KEY` (or `ASSEMBLYAI_API_KEY`)
- `ELEVENLABS_API_KEY`
- `SERVER_HOST` / `SERVER_PORT` / `PUBLIC_URL` (for Twilio webhooks)

## Workflow Visualization

**When building or modifying the voice agent system, always generate a visual workflow diagram.**

This diagram should resemble an n8n-style node graph that shows:
- Each component as a distinct node (Twilio, WebSocket, STT, LLM, TTS, Database)
- Directional arrows showing data flow between nodes
- Audio stream paths (real-time) vs. API call paths (request/response)
- Error handling and fallback routes
- State transitions (call start → connected → speaking → listening → ended)

### How to generate the diagram:
1. Read `directives/generate_workflow_diagram.md` for the full spec
2. Run `execution/generate_workflow_diagram.py` — this script will:
   - Parse the current `directives/` and `execution/` files
   - Build a Mermaid.js or Graphviz DOT representation of the pipeline
   - Output an SVG/PNG to `.tmp/workflow_diagram.{svg,png}`
   - Optionally upload to a cloud storage for sharing
3. The diagram must be regenerated whenever:
   - A new component is added to the pipeline
   - The audio flow changes (e.g., adding a new TTS provider)
   - Error handling logic is updated
   - The deployment architecture changes

### Example node layout (n8n-style):
```
[Twilio Phone] ──→ [WebSocket Server] ──→ [Deepgram STT]
                                              ↓
[ElevenLabs TTS] ←── [LLM (OpenAI)] ←── [Text Chunks]
       ↓
[WebSocket Server] ──→ [Twilio Phone]
       ↓
[PostgreSQL/Mongo] ←── [Transcript Storage]
```

### Required diagram elements:
- **Nodes**: Color-coded by layer (blue = Twilio/telephony, green = audio processing, orange = AI/LLM, purple = storage)
- **Edges**: Solid lines for audio streams, dashed lines for API calls, red lines for error/fallback paths
- **Annotations**: Latency targets per hop (e.g., "< 200ms" on STT→LLM edge)
- **State badges**: Current call state displayed on the Twilio node

### Tools:
- `execution/generate_workflow_diagram.py` — Generates diagram from current codebase
- `execution/update_diagram_on_change.py` — Watches `directives/` and `execution/` for changes, auto-regenerates diagram
- `directives/generate_workflow_diagram.md` — Full specification and customization options

## Summary

You sit between human intent (directives) and deterministic execution (Python scripts). Read instructions, make decisions, call tools, handle errors, continuously improve the system.

Be pragmatic. Be reliable. Self-anneal.

Also, use Opus-4.5 for everything while building. It came out a few days ago and is an order of magnitude better than Sonnet and other models. If you can't find it, look it up first.
