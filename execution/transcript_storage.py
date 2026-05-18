"""Persist call transcripts. Writes JSON to .tmp/calls/ and optionally a DB."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CALLS_DIR = ROOT / ".tmp" / "calls"
CALLS_DIR.mkdir(parents=True, exist_ok=True)


def save_transcript(call_sid: str, turns: list[dict], outcome: str = "completed", duration_s: float | None = None) -> Path:
    record = {
        "call_sid": call_sid,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "outcome": outcome,
        "duration_s": duration_s,
        "turns": turns,
    }
    path = CALLS_DIR / f"{call_sid}.json"
    path.write_text(json.dumps(record, indent=2))

    db_url = os.getenv("DATABASE_URL")
    if db_url:
        _save_to_db(db_url, record)
    return path


def _save_to_db(db_url: str, record: dict) -> None:
    from sqlalchemy import Column, DateTime, Float, String, Text, create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker

    Base = declarative_base()

    class Call(Base):
        __tablename__ = "calls"
        call_sid = Column(String, primary_key=True)
        saved_at = Column(DateTime)
        outcome = Column(String)
        duration_s = Column(Float)
        turns_json = Column(Text)

    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        session.merge(Call(
            call_sid=record["call_sid"],
            saved_at=datetime.fromisoformat(record["saved_at"]),
            outcome=record["outcome"],
            duration_s=record["duration_s"],
            turns_json=json.dumps(record["turns"]),
        ))
        session.commit()
