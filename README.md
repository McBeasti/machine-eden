# Machine Eden

Machine Eden is a self-evolving machine society simulator. Autonomous agents move, mine, harvest energy, and explore a procedurally generated world. Behaviour emerges from local rules and energy constraints, not scripted narratives.

## Project structure

```
Machine Colony/
├── backend/          # FastAPI server + simulation engine (Python)
├── frontend/         # React + Pixi.js visualization (TypeScript)
├── tests/            # Pytest suite
├── data/             # SQLite event persistence (gitignored)
└── docs/             # Architecture and experiment guides
```

## GitHub

The project is ready to publish. From the repository root:

```powershell
# 1. Authenticate (one-time)
gh auth login --web --git-protocol https

# 2. Create repo and push
.\scripts\publish-github.ps1
```

This creates a public repo named `machine-eden` and pushes the `main` branch. Edit `scripts/publish-github.ps1` to use `private` or a different name.

**Recommended:** clone to a local (non–Google Drive) folder for development — `node_modules` and `.venv` sync poorly on Drive.

## Quick start (test the app)

### Windows (Command Prompt)

1. Install [Python 3.11+](https://www.python.org/downloads/) and [Node.js 20+](https://nodejs.org/) if you do not have them.
2. Open **Command Prompt**, go to your clone of this repo, then run:

```bat
cd path\to\machine-eden
scripts\dev.cmd
```

Two windows open (backend + frontend). Then open **http://localhost:5173** in your browser.

### Windows (PowerShell)

```powershell
cd path\to\machine-eden
.\scripts\dev.ps1
```

### macOS / Linux

```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

Then open **http://localhost:5173**.

Or start the two processes yourself:

## Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- (Optional) PyTorch for Phase 2 ML experiments — see `backend/requirements-ml.txt`

## Backend setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API runs at `http://localhost:8000`. OpenAPI docs: `http://localhost:8000/docs`.

## Frontend setup

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

The UI runs at `http://localhost:5173` and proxies `/api` and `/ws` to the backend.

## Running tests

From the repository root:

```bash
cd backend
.venv\Scripts\activate   # or source .venv/bin/activate

cd ..
pytest
```

`pytest.ini` sets `testpaths=tests` and `pythonpath=backend`.

Test coverage includes determinism, energy and mining mechanics, movement, events, and REST API endpoints.

## Phase 1 status

Phase 1 — **Visual Foundation** — is implemented:

| Area | Status |
|------|--------|
| Simulation engine (world, agents, tick loop) | Done |
| Rule-based AI (energy, mining, exploration) | Done |
| FastAPI REST + WebSocket API | Done |
| SQLite event persistence | Done |
| React/Pixi world view, controls, analytics | Done |
| Config presets and metrics export | Done |
| Pytest suite | Done |
| PyTorch policy network | Placeholder (Phase 2) |
| Reproduction, combat, factions | Planned (Phase 2+) |

See `docs/` for architecture, simulation rules, event schema, and experiment guides.

## npm troubleshooting

### SSL certificate errors (`UNABLE_TO_GET_ISSUER_CERT_LOCALLY`)

Corporate proxies and custom root CAs often cause npm install failures. Use the system certificate store:

```bash
npm config set use-system-ca true
```

Then retry `npm install`. On Windows, ensure your organisation's root CA is installed in the system trust store.

### Google Drive and `node_modules`

This project may live on Google Drive (`G:\My Drive\...`). **Do not store `node_modules` on Google Drive.** Syncing thousands of small files is slow, can corrupt packages, and causes file-lock errors during install.

Recommended approaches:

1. **Install locally outside Drive** — clone or copy `frontend/` to a local path (e.g. `C:\dev\machine-eden\frontend`), run `npm install` there, and symlink or work from that copy.
2. **Exclude from sync** — if you must keep the repo on Drive, exclude `frontend/node_modules` from Google Drive sync (Drive for desktop → folder preferences).
3. **Use a junction on Windows** — keep source on Drive but redirect `node_modules` to a local folder:

   ```powershell
   cd frontend
   mklink /J node_modules C:\dev\machine-eden-cache\node_modules
   npm install
   ```

Always add `node_modules/` to `.gitignore` (already included). Re-run `npm install` after moving the project off Drive.

## Documentation

- [Architecture](docs/architecture.md)
- [Simulation rules](docs/simulation-rules.md)
- [Machine learning roadmap](docs/machine-learning.md)
- [Event schema](docs/event-schema.md)
- [Experiment guide](docs/experiment-guide.md)

## License

Private research project — all rights reserved unless otherwise noted.
