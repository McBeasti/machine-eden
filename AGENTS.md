# AGENTS.md

## Cursor Cloud specific instructions

Machine Eden has two services. Standard commands are in `README.md`; the notes below cover only non-obvious, durable caveats.

### Services

| Service | Location | Run (dev) | Notes |
|---------|----------|-----------|-------|
| Backend | `backend/` (FastAPI + simulation engine) | `backend/.venv/bin/uvicorn app.main:app --reload --port 8000` run from inside `backend/` | Serves REST at `/api`, WebSocket at `/ws/simulation`, Swagger UI at `/docs`. |
| Frontend | `frontend/` (React + Vite + Pixi.js) | `npm run dev --prefix frontend` | Dev server on `5173`, proxies `/api` and `/ws` to `localhost:8000` (see `vite.config.ts`). |

### Backend caveats
- Python deps live in a virtualenv at `backend/.venv` (created by the update script). Call tools directly (`backend/.venv/bin/pytest`, `backend/.venv/bin/uvicorn`) or activate with `source backend/.venv/bin/activate`.
- Run tests from the repo root: `backend/.venv/bin/pytest`. `pytest.ini` sets `testpaths=tests` and `pythonpath=backend`, so run pytest from root, not from `backend/`.
- Uvicorn must run with `backend/` as the working directory (or `--app-dir backend`) because `app.main` imports the top-level `app` and `simulation` packages.
- SQLite event DB is auto-created at `data/machine_eden.db` on backend startup (gitignored); no migration step is needed.

### Known pre-existing issues (not environment problems)
- `npm run lint` fails: the `lint` script runs `eslint .`, but ESLint is not in `frontend/package.json` devDependencies and there is no ESLint config. Linting is effectively not wired up.
- The frontend UI does not render (both `npm run dev` and `npm run build`): `frontend/src/components/WorldCanvas.tsx` imports from `./store` and `./types`, but those files are one level up. Sibling components correctly use `../store` / `../types`. Until this is fixed, Vite shows an import-resolution error overlay and no UI renders. The backend and its Swagger UI at `/docs` work fully and exercise the core simulation.
