"""Structured simulation event logging."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SimulationEvent:
    tick: int
    event_type: str
    actor_id: str | None = None
    location: tuple[int, int] | None = None
    actors: list[str] = field(default_factory=list)
    resources: dict[str, float] = field(default_factory=dict)
    outcome: str = "success"
    lineage_id: str | None = None
    faction_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.location:
            d["location"] = list(self.location)
        return d


class EventLog:
    """In-memory ring buffer plus optional persistence hook."""

    def __init__(self, max_buffer: int = 2000) -> None:
        self._buffer: deque[SimulationEvent] = deque(maxlen=max_buffer)
        self._all_events: list[SimulationEvent] = []
        self._persist_callback: Any = None

    def set_persist_callback(self, callback: Any) -> None:
        self._persist_callback = callback

    def emit(self, event: SimulationEvent) -> None:
        self._buffer.append(event)
        self._all_events.append(event)
        if self._persist_callback:
            self._persist_callback(event)

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        events = list(self._buffer)[-limit:]
        return [e.to_dict() for e in events]

    def since_tick(self, tick: int) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._all_events if e.tick >= tick]

    def count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self._all_events:
            counts[e.event_type] = counts.get(e.event_type, 0) + 1
        return counts

    def clear(self) -> None:
        self._buffer.clear()
        self._all_events.clear()

    def export_json(self) -> str:
        return json.dumps([e.to_dict() for e in self._all_events], indent=2)
