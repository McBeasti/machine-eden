# Simulation Rules

This document describes the Phase 1 simulation mechanics implemented in `backend/simulation/`.

## World

The world is a 2D grid (`world_width` × `world_height`, default 128×128). Each cell has:

- **Terrain type** — empty, mineral, metal, rare, energy source, charging station, hazard, abandoned
- **Resource quantity** — depletable stock on mineable cells
- **Movement cost** — higher on hazard terrain
- **Hazard level** — environmental damage per tick
- **Signal quality** — affects future communication (Phase 3)

Worlds are procedurally generated from `SimulationConfig` and `seed`.

### Terrain summary

| Terrain | Purpose |
|---------|---------|
| Mineral / Metal / Rare | Mineable resources |
| Energy source | Passive energy harvest |
| Charging station | Fast recharge |
| Hazard | Damage and movement penalty |
| Abandoned | Low-yield salvage mining |

Resources on mineral and energy cells regenerate over time at `renewable_rate`.

## Agents

Each agent has:

- **Hardware** — speed, sensors, energy capacity, mining ability, etc.
- **Software** — behavioural tendencies (cooperation, exploration, aggression, …)
- **Energy** — spent on actions and idle upkeep; death at zero
- **Inventory** — mined resources up to `carrying_capacity`
- **Visit map** — exploration memory for least-visited movement

New agents spawn at `initial_population` on reset, placed randomly with lineage IDs.

## Actions (Phase 1)

| Action | Energy cost (base) | Effect |
|--------|-------------------|--------|
| Idle | 0.05 × consumption × scarcity | No movement |
| Move | 0.5 + distance × 0.3 × terrain cost × scarcity | Move one cell toward target |
| Mine | 1.5 × scarcity | Extract resources from current cell |
| Harvest | 0.3 × scarcity | Gain energy on energy source |
| Recharge | 0.1 × scarcity | Gain energy on charging station |

`energy_scarcity` scales all costs globally.

### Mining

- Requires `mining_ability > 0` and mineable terrain with resources > 0.5
- Yield = `min(MINE_BASE_YIELD × mining_ability, available)` (default base 2.0)

### Death

When energy ≤ 0:

1. Agent marked dead; inventory drops 50% to the cell
2. `death` and optional `drop` events emitted
3. Agent removed from spatial index

Environmental hazard also drains energy and adds damage each tick.

## Decision engine (Phase 1)

Rule-based priority in `ai/rules.py`:

1. **Recharge** — on charging station if energy < 95%
2. **Harvest** — on energy source if energy < 85%
3. **Emergency seek** — energy < 25%; move toward nearest station or source
4. **Mine** — on mineable cell with inventory space
5. **Seek resources** — move toward nearest mineable cell
6. **Seek energy** — energy < 50%; move toward power
7. **Explore** — move to least-visited neighbour (weighted by `exploration_tendency`)

Each choice records a `DecisionRecord` (inputs, scores, goal, interpretation) for the UI and analysis.

## Metrics

Per-tick aggregates include population, births, deaths, energy consumed/produced, mining volume, and mean agent energy. History is exposed via `/api/metrics` and WebSocket deltas.

## Configuration presets

Named presets in `config.py` override subsets of parameters:

- `resource_abundance`, `energy_crisis`, `high_mutation`
- `hostile_world`, `cooperative_incentives`, `competitive_incentives`
- `isolated_regions`, `dense_megastructure`

Apply via `POST /api/presets/apply` with `{"preset": "energy_crisis"}`.

## Not yet implemented (Phase 2+)

- Reproduction and offspring mutation
- Attack, repair, construction
- Faction loyalty and communication
- Neural policy replacing rule tree
