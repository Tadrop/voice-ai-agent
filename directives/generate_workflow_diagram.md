# Directive: Generate Workflow Diagram

## Goal
Render an up-to-date, n8n-style node graph of the voice pipeline whenever components or flow change.

## Inputs
- Current state of `directives/` and `execution/`

## Tools
- `execution/generate_workflow_diagram.py` — emits Mermaid + Graphviz DOT, renders to SVG/PNG
- `execution/update_diagram_on_change.py` — watchdog-based file watcher

## Outputs
- `.tmp/workflow_diagram.svg`
- `.tmp/workflow_diagram.png`
- `.tmp/workflow_diagram.mmd` (Mermaid source — can be pasted into docs)

## Style
- **Nodes** color-coded by layer:
  - blue — Twilio / telephony
  - green — audio processing (STT, resampler)
  - orange — AI / LLM
  - purple — storage
- **Edges**:
  - solid — real-time audio
  - dashed — request/response API calls
  - red — error / fallback
- **Annotations**: latency targets per hop (e.g. `< 200ms`)
- **State badge** on Twilio node: idle | ringing | speaking | listening | ended

## Regenerate when
- New component is added (e.g., new TTS provider)
- Audio flow changes
- Error handling logic changes
- Deployment architecture changes
