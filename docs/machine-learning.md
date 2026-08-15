# Machine Learning

Machine Eden is designed to evolve agent behaviour through simulation. Phase 1 uses hand-written rules; Phase 2 introduces learnable policies.

## Current state (Phase 1)

Agents are controlled by `simulation/ai/rules.py` — a deterministic priority tree over energy, inventory, and local terrain. No model training runs in Phase 1.

`simulation/ai/policy.py` defines a **placeholder** `PolicyNetwork`:

- Input size: 16 (planned observation vector)
- Output size: 8 (planned action logits)
- Architecture: 16 → 32 → 16 → 8 with ReLU and Tanh
- Requires PyTorch (`requirements-ml.txt`)

If `torch` is not installed, importing `PolicyNetwork` raises a clear error pointing to the ML requirements file.

## Planned Phase 2 pipeline

### Observation vector (target)

Planned inputs for the policy (16 dimensions):

| Index | Feature |
|-------|---------|
| 0–1 | Normalised position (x, y) |
| 2 | Energy ratio |
| 3 | Damage ratio |
| 4 | Inventory fill ratio |
| 5–8 | Nearest resource/energy distances (normalised) |
| 9–12 | Local terrain one-hot or embedding |
| 13–15 | Software tendencies (cooperation, exploration, aggression) |

Exact encoding will be finalised when the policy replaces the rule engine.

### Action space

Phase 1 actions map to policy outputs:

- Move (8 directions + stay)
- Mine, harvest, recharge, idle

The network outputs continuous scores; argmax or sampling selects the action.

### Training approach (planned)

1. **Neuroevolution** — mutate policy weights on reproduction; fitness = survival time + resource gathered
2. **Imitation (optional)** — warm-start from Phase 1 decision logs (`DecisionRecord`)
3. **Batch experiments** — headless runs with fixed seeds; compare lineages across presets

### Dependencies

```bash
cd backend
pip install -r requirements-ml.txt
```

This installs `torch>=2.5.0` in addition to core requirements.

## Experiment integration

- Export decision logs via agent detail API (`/api/agents/{id}`)
- Export events and metrics for offline training (`/api/export/events`, `/api/export/metrics`)
- Use `SimulationConfig.seed` for reproducible train/eval splits

See [Experiment guide](experiment-guide.md) for running comparative runs.

## Design principles

1. **Simulation-first** — ML serves emergent behaviour, not scripted outcomes
2. **Inspectable** — decisions and events remain structured and logged
3. **Optional** — core sim runs without PyTorch installed
4. **Deterministic eval** — fixed seeds for comparing policies across runs
