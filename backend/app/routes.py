"""REST API routes."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.simulation_manager import manager
from simulation.config import PRESETS, SimulationConfig

router = APIRouter(prefix="/api")


class ConfigUpdate(BaseModel):
    seed: int | None = None
    world_width: int | None = None
    world_height: int | None = None
    initial_population: int | None = None
    resource_density: float | None = None
    renewable_rate: float | None = None
    mutation_rate: float | None = None
    environmental_danger: float | None = None
    energy_scarcity: float | None = None
    max_agents: int | None = None
    ticks_per_second: float | None = None
    charging_station_density: float | None = None
    energy_source_density: float | None = None
    hazard_density: float | None = None


class SpeedUpdate(BaseModel):
    multiplier: float


class PresetRequest(BaseModel):
    preset: str


@router.get("/health")
def health():
    return {"status": "ok", "service": "machine-eden"}


@router.get("/simulation/state")
def get_state():
    return manager.engine.get_state()


@router.get("/simulation/config")
def get_config():
    return manager.engine.config.model_dump()


@router.post("/simulation/config")
def update_config(body: ConfigUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    config = manager.update_config(updates)
    return config.model_dump()


@router.post("/simulation/reset")
async def reset_simulation(body: ConfigUpdate | None = None):
    config = None
    if body:
        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        if updates:
            manager.update_config(updates)
            config = manager.engine.config
    return manager.reset(config)


@router.post("/simulation/start")
async def start_simulation():
    # async so manager.start() can schedule the tick loop on this event loop
    manager.start()
    return {"running": True}


@router.post("/simulation/pause")
async def pause_simulation():
    manager.pause()
    return {"running": False}


@router.post("/simulation/step")
async def step_simulation():
    delta = manager.step_once()
    return delta


@router.post("/simulation/speed")
async def set_speed(body: SpeedUpdate):
    manager.set_speed(body.multiplier)
    return {"speed": manager.engine.speed_multiplier}


@router.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    agent = manager.engine.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/events")
def get_events(limit: int = 100, since_tick: int | None = None):
    if since_tick is not None:
        return manager.engine.events.since_tick(since_tick)[-limit:]
    return manager.engine.events.recent(limit)


@router.get("/metrics")
def get_metrics(last_n: int | None = 200):
    return manager.engine.metrics.get_history(last_n)


@router.get("/presets")
def list_presets():
    return {"presets": list(PRESETS.keys())}


@router.post("/presets/apply")
def apply_preset_route(body: PresetRequest):
    if body.preset not in PRESETS:
        raise HTTPException(status_code=400, detail=f"Unknown preset: {body.preset}")
    config = manager.apply_preset(body.preset)
    return config.model_dump()


@router.get("/export/metrics")
def export_metrics(format: str = "json"):
    history = manager.engine.metrics.get_history()
    if format == "csv":
        if not history:
            return PlainTextResponse("", media_type="text/csv")
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=history[0].keys())
        writer.writeheader()
        writer.writerows(history)
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return history


@router.get("/export/events")
def export_events(format: str = "json"):
    events = manager.engine.events.recent(10000)
    if format == "csv":
        output = io.StringIO()
        if events:
            writer = csv.DictWriter(output, fieldnames=["tick", "event_type", "actor_id", "outcome"])
            writer.writeheader()
            for e in events:
                writer.writerow({k: e.get(k, "") for k in ["tick", "event_type", "actor_id", "outcome"]})
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return events
