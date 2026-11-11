---
milestone: Render Deployment Readiness
version: 1.0
updated: 2026-11-10
---

# Roadmap

> **Current Phase:** 1 - Render packaging and runtime readiness
> **Status:** executing

## Must-Haves

- [ ] Frontend TypeScript/Vite production build succeeds.
- [ ] Render can build and run the full application from one web service.
- [ ] PostgreSQL URLs and Alembic migrations work with Render's managed database.
- [ ] Health reporting distinguishes liveness and dependency readiness.
- [ ] Voice and text agent workflow remains unchanged.

## Phase 1: Render Packaging and Runtime Readiness

**Status:** In Progress
**Objective:** Package the current app for Render and correct production build and startup integration.

### Plan 1.1: Build, database, and deployment integration

- [ ] Add Vite env typing and verify frontend build.
- [ ] Add single-service Docker/Render config and serve the built UI from FastAPI.
- [ ] Normalize Render PostgreSQL URLs and make Alembic use its async driver.
- [ ] Add readiness reporting and document deployment setup.

