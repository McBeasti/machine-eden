# Architecture

Machine Eden is a client–server simulation with a Python backend and a React frontend. The backend owns all game state; the frontend renders and controls the run.

## High-level diagram

```
┌─────────────────┐     REST / WebSocket      ┌──────────────────────────┐
│  React + Pixi   │ ◄────────────────────────► │  FastAPI (app/)          │
│  frontend/      │   /api/*  /ws/simulation   │  SimulationManager       │
└─────────────────┘                            └────────────┬─────────────┘
                                                           │
                                                           ▼
                                              ┌──────────────────────────┐
                                              │  SimulationEngine          │
                                              │  world · agents · metrics  │
                                              │  events · decisions        │
                                              └────────────┬─────────────┘
                                                           │
                                                           ▼
                                              ┌──────────────────────────┐
                                              │  SQLite (data/*.db)        │
                                              │  event persistence         │
                                              └──────────────────────────┘
```

## Backend layers

### `app/` — API layer

| Module | Role |
|--------|------|
| `main.py` | FastAPI app, CORS, WebSocket endpoint |
| `routes.py` | REST routes for state, config, agents, metrics, exports |
| `simulation_manager.py` | Singleton wrapping the engine; async tick loop; WebSocket broadcast |
| `database.py` | SQLAlchemy models; persists events to `data/machine_eden.db` |

### `simulation/` — Core simulation

| Module | Role |
|--------|------|
| `engine.py` | Tick loop: decide → act → regenerate → metrics |
| `world.py` | 2D grid: terrain, resources, hazards, procedural generation |
| `agent.py` | Agent identity, hardware, software, inventory, energy |
| `actions.py` | Action types, energy costs, validation helpers |
| `config.py` | `SimulationConfig`, reward profiles, named presets |
| `events.py` | Structured `SimulationEvent` log (ring buffer + export) |
| `decisions.py` | Per-agent decision records for inspection |
| `metrics.py` | Population, energy, mining aggregates per tick |
| `spatial.py` | Spatial index for neighbour queries |
| `ai/rules.py` | Phase 1 rule-based decision tree |
| `ai/policy.py` | Phase 2 PyTorch policy placeholder |

## Frontend

Built with Vite, React 18, Pixi.js 8, Zustand, and Recharts.

| Component | Role |
|-----------|------|
| `WorldCanvas.tsx` | Pixi renderer for terrain and agents |
| `Controls.tsx` | Start, pause, step, speed, presets |
| `AgentPanel.tsx` | Selected agent detail and event log |
| `Analytics.tsx` | Metrics charts |
| `store.ts` | WebSocket connection and state sync |

Vite proxies `/api` and `/ws` to `localhost:8000` during development.

## Data flow

1. **Initial load** — WebSocket sends full `state` snapshot (world grid, agents, config, metrics history).
2. **Running** — Manager loop calls `engine.step()` at `ticks_per_second × speed_multiplier`; each tick broadcasts a `tick` delta (agents, metrics, recent events).
3. **Manual step** — REST `POST /api/simulation/step` or WebSocket `action: step`.
4. **Persistence** — Every emitted event is written to SQLite via `persist_event`.

## Determinism

Given the same `SimulationConfig.seed`, world generation and agent RNG streams are reproducible. Agent processing order is sorted by ID each tick for stable results (see `tests/test_determinism.py`).

## Phase roadmap

| Phase | Focus |
|-------|--------|
| **1** (current) | Rule-based agents, visualization, metrics, API |
| **2** | Neural policies, mutation, reproduction |
| **3** | Factions, communication, construction |
| **4** | Long-run experiments and comparative analysis |
