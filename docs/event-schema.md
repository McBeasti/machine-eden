# Event Schema

Simulation events are structured records emitted by `SimulationEngine` and stored in memory, SQLite, and API responses.

## Core type

Defined in `simulation/events.py` as `SimulationEvent`:

```json
{
  "tick": 42,
  "event_type": "move",
  "actor_id": "agent-a1b2c3",
  "location": [64, 32],
  "actors": ["agent-a1b2c3"],
  "resources": {},
  "outcome": "success",
  "lineage_id": "lineage-xyz",
  "faction_id": null,
  "metadata": { "from": [63, 32] }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tick` | int | yes | Simulation tick when the event occurred |
| `event_type` | string | yes | Event category (see below) |
| `actor_id` | string \| null | no | Primary agent involved |
| `location` | `[x, y]` \| null | no | Grid coordinates |
| `actors` | string[] | no | All agents involved |
| `resources` | object | no | Resource deltas (name → amount) |
| `outcome` | string | no | Result label (default `"success"`) |
| `lineage_id` | string \| null | no | Agent lineage for genealogy |
| `faction_id` | string \| null | no | Reserved for Phase 3 factions |
| `metadata` | object | no | Event-specific extra data |

## Event types (Phase 1)

| `event_type` | When emitted | Typical `resources` / `metadata` |
|--------------|--------------|-----------------------------------|
| `spawn` | Agent created on reset | `lineage_id` |
| `move` | Agent moves to adjacent cell | `metadata.from` = previous `[x, y]` |
| `mine` | Successful mining action | `resources` = `{mineral\|metal\|rare: amount}` |
| `harvest` | Energy harvested from source | `resources.energy` |
| `recharge` | Energy gained at station | `resources.energy` |
| `regenerate` | World cell regained resources | `resources.amount`, `metadata.terrain` |
| `drop` | Inventory scattered on death | full inventory dict |
| `death` | Agent energy depleted | `outcome`: `"energy_depletion"`, `metadata.age` |

Future phases may add `reproduce`, `attack`, `communicate`, `build`, etc.

## Storage

### In-memory

`EventLog` keeps:

- Ring buffer (default 2000 events) for recent API reads
- Full list for export and `since_tick` queries

### SQLite

`app/database.py` persists each event as:

| Column | Content |
|--------|---------|
| `tick` | int |
| `event_type` | string |
| `payload` | JSON string of full event dict |
| `created_at` | UTC timestamp |

Database path: `data/machine_eden.db` (gitignored).

## API access

| Endpoint | Description |
|----------|-------------|
| `GET /api/events?limit=100` | Recent events |
| `GET /api/events?since_tick=500&limit=200` | Events from tick onward |
| `GET /api/export/events?format=json` | Bulk export (up to 10k recent) |
| `GET /api/export/events?format=csv` | CSV with tick, type, actor, outcome |

WebSocket `tick` messages include the 50 most recent events in each delta.

## Export example

```bash
curl http://localhost:8000/api/export/events > events.json
curl "http://localhost:8000/api/export/events?format=csv" > events.csv
```

## Validation notes

- Locations are serialised as `[x, y]` lists in JSON (tuples converted in `to_dict()`)
- Empty optional fields may be omitted or null depending on serialisation context
- Event order within a tick follows agent processing order (sorted agent IDs)
