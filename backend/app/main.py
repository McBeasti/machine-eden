"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router
from app.simulation_manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Machine Eden",
    description="Self-Evolving Machine Society Simulator API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.websocket("/ws/simulation")
async def simulation_ws(websocket: WebSocket):
    await websocket.accept()
    manager.subscribe(websocket)
    try:
        await websocket.send_json({"type": "state", "data": manager.engine.get_state()})
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                action = msg.get("action")
                if action == "start":
                    manager.start()
                elif action == "pause":
                    manager.pause()
                elif action == "step":
                    delta = manager.step_once()
                    await websocket.send_json({"type": "tick", "data": delta})
                elif action == "reset":
                    state = manager.reset()
                    await websocket.send_json({"type": "state", "data": state})
                elif action == "speed":
                    manager.set_speed(msg.get("multiplier", 1.0))
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.unsubscribe(websocket)
