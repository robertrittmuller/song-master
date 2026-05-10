# Song Master Development Guidelines

## Scope

Song Master is a container-first full-stack app:
- Backend: [backend/app/main.py](backend/app/main.py), with API routes under [backend/app/api/routes/](backend/app/api/routes/) and services under [backend/app/services/](backend/app/services/)
- CLI: [cli/song_master.py](cli/song_master.py)
- Frontend: [frontend/src/main.tsx](frontend/src/main.tsx), [frontend/src/App.tsx](frontend/src/App.tsx), and [frontend/src/services/api.ts](frontend/src/services/api.ts)

Use [docs/web-gui-architecture.md](docs/web-gui-architecture.md) and [docs/web-gui-requirements.md](docs/web-gui-requirements.md) for GUI context, but verify behavior against the code because older plans and docs can be stale.

## Local Workflow

- Use Docker Compose for all local work. Do not rely on a local venv or conda environment for this project.
- Start the stack from the repo root with `docker compose up` or `docker-compose up`, depending on which Compose command is available in the environment.
- Build images with `docker compose build`.
- Run frontend package commands inside the frontend container. The host shell may not have `npm` available.
- Install frontend dependencies with `docker compose exec frontend npm install`.
- Build the frontend with `docker compose exec frontend npm run build`.
- Verify backend behavior with `docker compose exec backend python -m unittest discover tests`.
- If you add a new test style, update the repo instructions at the same time so agents do not guess.

## What To Check First

- The live backend health route is `/healthz`; the healthcheck in [Dockerfile.backend](Dockerfile.backend) is stale.
- Backend auth is bearer-token/JWT based.
- Settings are read-only from the API and are assembled server-side.
- The frontend `package.json` currently has no real `test` script, and `npm run lint` is only a placeholder.

## Working Conventions

- Use absolute imports in Python.
- Keep public Python functions and classes documented with Google-style docstrings and type hints.
- Use functional React components and hooks in the frontend.
- Prefer small, focused edits that stay within the owning layer.
- Link to existing docs instead of copying their contents into instructions or comments.
- Treat `plans/` as historical context unless the task explicitly calls for those files.

## Repo-Specific Notes

- Demo-track audio generation must be sanitized at request time before MiniMax submission.
- For clipboard actions in the frontend, use [frontend/src/services/clipboard.ts](frontend/src/services/clipboard.ts) instead of direct `navigator.clipboard` access.