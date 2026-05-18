"""Watch directives/ and execution/ and regenerate the workflow diagram on change.

Run: python execution/update_diagram_on_change.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

ROOT = Path(__file__).resolve().parent.parent
WATCH = [ROOT / "directives", ROOT / "execution"]


class Regenerator(FileSystemEventHandler):
    def __init__(self) -> None:
        self.last = 0.0

    def on_any_event(self, event) -> None:
        if event.is_directory:
            return
        now = time.time()
        if now - self.last < 1.0:
            return
        self.last = now
        print(f"[watch] change: {event.src_path} → regenerating")
        subprocess.run([sys.executable, str(ROOT / "execution" / "generate_workflow_diagram.py")], check=False)


def main() -> int:
    handler = Regenerator()
    obs = Observer()
    for p in WATCH:
        if p.exists():
            obs.schedule(handler, str(p), recursive=True)
    obs.start()
    print("Watching:", [str(p) for p in WATCH])
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())
