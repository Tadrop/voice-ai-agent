"""Generate the n8n-style workflow diagram of the voice pipeline.

Run: python execution/generate_workflow_diagram.py
Outputs:
  .tmp/workflow_diagram.mmd  (Mermaid source)
  .tmp/workflow_diagram.svg
  .tmp/workflow_diagram.png  (if graphviz binary is installed)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".tmp"
OUT.mkdir(parents=True, exist_ok=True)


MERMAID = """flowchart LR
    classDef telephony fill:#cfe5ff,stroke:#1f6feb,color:#0b1f3a;
    classDef audio fill:#d3f5d8,stroke:#1f883d,color:#0a2b14;
    classDef ai fill:#ffe1bf,stroke:#bf6a02,color:#3a1f00;
    classDef storage fill:#e8dcff,stroke:#6f42c1,color:#1f0a3a;

    Phone([Caller Phone]):::telephony
    Twilio[Twilio Media Streams]:::telephony
    WS[WebSocket Server /ws]:::telephony
    STT[Deepgram STT]:::audio
    LLM[LLM Orchestrator<br/>OpenAI gpt-4o]:::ai
    TTS[ElevenLabs TTS]:::audio
    DB[(Transcript Storage)]:::storage

    Phone == audio ==> Twilio
    Twilio == mulaw 8k ==> WS
    WS == frames ==> STT
    STT -. partial/final .-> LLM
    LLM -. tokens .-> TTS
    TTS == mulaw 8k ==> WS
    WS == audio ==> Twilio
    Twilio == audio ==> Phone
    WS -. transcript .-> DB

    %% latency targets
    linkStyle 2 stroke:#1f883d,stroke-width:2px
    linkStyle 3 stroke:#bf6a02,stroke-dasharray:6 4
    linkStyle 4 stroke:#bf6a02,stroke-dasharray:6 4
"""

DOT = """digraph voice_agent {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fontname="Helvetica"];

  Phone   [label="Caller Phone",          fillcolor="#cfe5ff"];
  Twilio  [label="Twilio Media Streams",  fillcolor="#cfe5ff"];
  WS      [label="WebSocket Server /ws",  fillcolor="#cfe5ff"];
  STT     [label="Deepgram STT",          fillcolor="#d3f5d8"];
  LLM     [label="LLM Orchestrator",      fillcolor="#ffe1bf"];
  TTS     [label="ElevenLabs TTS",        fillcolor="#d3f5d8"];
  DB      [label="Transcript Storage",    fillcolor="#e8dcff", shape=cylinder];

  Phone  -> Twilio [label="audio"];
  Twilio -> WS     [label="mulaw 8k"];
  WS     -> STT    [label="frames  (<200ms)"];
  STT    -> LLM    [label="text",  style=dashed];
  LLM    -> TTS    [label="tokens",style=dashed];
  TTS    -> WS     [label="mulaw 8k"];
  WS     -> Twilio [label="audio"];
  Twilio -> Phone  [label="audio"];
  WS     -> DB     [label="transcript", style=dashed];
}
"""


def main() -> int:
    mmd_path = OUT / "workflow_diagram.mmd"
    mmd_path.write_text(MERMAID)
    print(f"Wrote {mmd_path}")

    dot_path = OUT / "workflow_diagram.dot"
    dot_path.write_text(DOT)
    print(f"Wrote {dot_path}")

    try:
        from graphviz import Source
        src = Source(DOT)
        svg = src.pipe(format="svg")
        (OUT / "workflow_diagram.svg").write_bytes(svg)
        print(f"Wrote {OUT / 'workflow_diagram.svg'}")
        try:
            png = src.pipe(format="png")
            (OUT / "workflow_diagram.png").write_bytes(png)
            print(f"Wrote {OUT / 'workflow_diagram.png'}")
        except Exception as e:
            print(f"PNG render skipped ({e}). Install graphviz binary for PNG output.")
    except Exception as e:
        print(f"Graphviz render skipped ({e}). Mermaid + DOT sources still written.")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
