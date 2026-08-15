"""Simulation manager singleton for API layer."""

from __future__ import annotations

import asyncio
from typing import Any

from app.database import init_db, persist_event
from simulation.config import SimulationConfig, apply_preset
from simulation.engine import SimulationEngine
from simulation.events import SimulationEvent


class SimulationManager:
    """Wraps engine with async loop and WebSocket broadcasting."""

    def __init__(self) -> None:
        init_db()
        self.engine = SimulationEngine()
        self._task: asyncio.Task | None = None
        self._subscribers: list[Any] = []
        self._setup_persistence()

    def _setup_persistence(self) -> None:
        def on_event(event: SimulationEvent) -> None:
            persist_event(event.to_dict())

        self.engine.events.set_persist_callback(on_event)

    def subscribe(self, websocket) -> None:
        self._subscribers.append(websocket)

    def unsubscribe(self, websocket) -> None:
        if websocket in self._subscribers:
            self._subscribers.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        dead = []
        for ws in self._subscribers:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.unsubscribe(ws)

    async def _run_loop(self) -> None:
        while self.engine.running:
            delta = self.engine.step()
            await self.broadcast({"type": "tick", "data": delta})
            interval = 1.0 / (self.engine.config.ticks_per_second * self.engine.speed_multiplier)
            await asyncio.sleep(max(0.01, interval))

    def start(self) -> None:
        if not self.engine.running:
            self.engine.running = True
            try:
                loop = asyncio.get_running_loop()
                self._task = loop.create_task(self._run_loop())
            except RuntimeError:
                # No event loop (e.g. sync test context) — flag only
                pass

    def pause(self) -> None:
        self.engine.running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def step_once(self) -> dict:
        return self.engine.step()

    def reset(self, config: SimulationConfig | None = None) -> dict:
        self.pause()
        self.engine.reset(config)
        return self.engine.get_state()

    def set_speed(self, multiplier: float) -> None:
        self.engine.speed_multiplier = max(0.25, min(8.0, multiplier))

    def update_config(self, updates: dict) -> SimulationConfig:
        data = self.engine.config.model_dump()
        data.update(updates)
        self.engine.config = SimulationConfig(**data)
        return self.engine.config

    def apply_preset(self, name: str) -> SimulationConfig:
        self.engine.config = apply_preset(name, self.engine.config)
        return self.engine.config


manager = SimulationManager()
