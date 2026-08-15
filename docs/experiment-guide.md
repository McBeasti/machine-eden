# Experiment Guide

How to run controlled simulation experiments with Machine Eden.

## Quick start

1. Start the backend (`uvicorn app.main:app --reload --app-dir backend`)
2. Start the frontend (`npm run dev` in `frontend/`) or use the REST API only
3. Reset with a known seed, run N ticks, export metrics and events

## Reproducibility

Set an explicit seed before reset:

```bash
curl -X POST http://localhost:8000/api/simulation/reset \
  -H "Content-Type: application/json" \
  -d '{"seed": 42, "world_width": 64, "world_height": 64, "initial_population": 40}'
```

The same seed and config produce identical initial worlds and RNG streams. Agent tick order is deterministic (sorted by ID).

Verify with:

```bash
pytest tests/test_determinism.py -v
```

## Headless batch runs (Python)

```python
from simulation.config import SimulationConfig, apply_preset
from simulation.engine import SimulationEngine

config = apply_preset("energy_crisis", SimulationConfig(seed=123))
engine = SimulationEngine(config)

for _ in range(1000):
    engine.step()

history = engine.metrics.get_history()
events = engine.events.export_json()
print(history[-1])  # final tick metrics
```

No server required — useful for overnight sweeps.

## Using presets

List available presets:

```bash
curl http://localhost:8000/api/presets
```

Apply one (updates config; call reset to regenerate world):

```bash
curl -X POST http://localhost:8000/api/presets/apply \
  -H "Content-Type: application/json" \
  -d '{"preset": "hostile_world"}'

curl -X POST http://localhost:8000/api/simulation/reset
```

### Suggested experiment matrix

| Variable | Presets / knobs |
|----------|-----------------|
| Resource abundance | `resource_abundance` vs `energy_crisis` |
| Environment | default vs `hostile_world` |
| Population density | `dense_megastructure` vs `isolated_regions` |
| Incentive framing | `cooperative_incentives` vs `competitive_incentives` |
| Mutation (Phase 2) | default vs `high_mutation` |

Run each condition with 3–5 seeds and compare survival curves from exported metrics.

## Metrics to track

Key fields in `/api/metrics` history:

- `population` — alive agents
- `deaths` / `births` — per-tick counters (births active in Phase 2+)
- `mean_energy` — population health
- `energy_consumed` / `energy_produced` — economy balance
- `resources_mined` — extraction rate

Export for analysis:

```bash
curl http://localhost:8000/api/export/metrics > metrics.json
curl "http://localhost:8000/api/export/metrics?format=csv" > metrics.csv
```

## Event analysis

Export full event logs for process tracing:

```bash
curl http://localhost:8000/api/export/events > events.json
```

Useful queries:

- Count `death` events by tick → survival analysis
- Sum `mine` `resources` by type → depletion dynamics
- Filter `move` events for exploration radius estimates

## Speed and duration

- Default: 10 ticks/second (`ticks_per_second` in config)
- Speed multiplier: 0.25×–8× via `POST /api/simulation/speed`
- Manual stepping: `POST /api/simulation/step` for exact tick control

For long runs, prefer headless Python over WebSocket to avoid browser timeouts.

## Recording UI sessions

Screenshot placeholder path: `docs/screenshots/world-view-placeholder.png`

Replace with actual captures from the world view for reports and papers.

## Checklist for a published run

- [ ] Record `SimulationConfig` JSON (`GET /api/simulation/config`)
- [ ] Note git commit hash or version (`Machine Eden v0.1`)
- [ ] Fixed seed documented
- [ ] Tick count and preset name recorded
- [ ] Metrics and events exported
- [ ] Pytest pass on same commit (`pytest`)

## Troubleshooting experiments

| Issue | Fix |
|-------|-----|
| Different results same seed | Ensure config identical; no concurrent resets |
| Population crashes immediately | Try `resource_abundance` or lower `energy_scarcity` |
| Slow runs | Reduce `world_width/height` or increase `speed` |
| DB locked | Single writer; close other processes using `data/machine_eden.db` |
