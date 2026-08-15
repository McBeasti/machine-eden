"""SQLAlchemy database models."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

# On Vercel the filesystem is ephemeral; keep SQLite under /tmp.
if os.environ.get("VERCEL"):
    DATA_DIR = Path("/tmp/machine-eden")
else:
    DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "machine_eden.db"


class Base(DeclarativeBase):
    pass


class EventRecord(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tick: Mapped[int] = mapped_column(Integer, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    Base.metadata.create_all(engine)


def persist_event(event_dict: dict) -> None:
    session = SessionLocal()
    try:
        record = EventRecord(
            tick=event_dict.get("tick", 0),
            event_type=event_dict.get("event_type", "unknown"),
            payload=json.dumps(event_dict),
        )
        session.add(record)
        session.commit()
    finally:
        session.close()
