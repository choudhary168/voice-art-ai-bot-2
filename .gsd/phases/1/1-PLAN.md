---
phase: 1
plan: 1
wave: 1
gap_closure: false
---

# Plan 1.1: Build, database, and deployment integration

## Objective

Make the existing voice agent deployable as one Render web service with a managed PostgreSQL database while preserving existing conversation behavior.

## Context

- `.gsd/SPEC.md`
- `backend/main.py`
- `backend/config.py`
- `backend/database/connection.py`
- `backend/database/migrations/env.py`
- `frontend/tsconfig.json`
- `frontend/src/App.tsx`

## Tasks

<task type="auto">
  <name>Fix the frontend build and serve its production bundle</name>
  <files>frontend/src/vite-env.d.ts, backend/main.py, Dockerfile</files>
  <action>Add the Vite client type reference, use a multi-stage Docker build for the frontend bundle, and mount that bundle from FastAPI after API/WebSocket routes. Keep REST and WebSocket same-origin in production.</action>
  <verify>Run `npm run build` from `frontend` and build the Docker image if Docker is available.</verify>
  <done>The TypeScript/Vite frontend build succeeds and the production container includes the built UI.</done>
</task>

<task type="auto">
  <name>Wire Render PostgreSQL, migration, and health configuration</name>
  <files>backend/config.py, backend/database/migrations/env.py, render.yaml, README.md</files>
  <action>Normalize Render's postgresql URL to asyncpg, keep Alembic on its async dialect, add an idempotent startup migration in the single-instance Render container, define Render web and database services, and distinguish liveness from readiness without changing agent session behavior.</action>
  <verify>Inspect the finalized Blueprint, run the frontend production build, and validate Python imports/configuration without accessing or mutating external services.</verify>
  <done>Render configuration is documented, migration uses asyncpg, and health status exposes persistence readiness separately from liveness.</done>
</task>

## Must-Haves

- [ ] Production frontend compiles.
- [ ] Render service binds the assigned port and serves REST, WebSocket, and UI on the same origin.
- [ ] Render's Postgres URL works with the async SQLAlchemy engine and existing Alembic migration.
- [ ] Health endpoints distinguish liveness from readiness.
- [ ] Conversation behavior remains unchanged.

## Success Criteria

- [ ] All tasks verified.
- [ ] No agent workflow or conversation semantics changed.
