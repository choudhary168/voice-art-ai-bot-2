# Render Deployment Readiness

**Status: FINALIZED**

## Objective

Prepare the existing Gemini voice agent for deployment on Render without changing the user-facing agent workflow or conversation behavior.

## Requirements

1. The frontend production build must compile successfully with its Vite environment variables typed correctly.
2. Provide a Render deployment configuration for the backend, frontend, and PostgreSQL persistence, with correct build/start commands and runtime port handling.
3. Configure the frontend to reach the deployed backend REST and WebSocket endpoints, including secure WebSockets in production, and configure backend CORS for the deployed frontend.
4. Apply the existing Alembic schema migration as part of deployment in a safe, repeatable way.
5. Make health reporting suitable for Render checks and distinguish service liveness from database persistence readiness.
6. Document the Render setup and required secrets/environment variables. Do not commit credentials.
7. Preserve the existing voice, text, session, and fallback behavior. Do not redesign or alter the conversation flow.
8. Verify the frontend build and deployment configuration statically; do not deploy or make external account changes.

## Acceptance Criteria

- Frontend production build completes successfully.
- Render configuration defines services and environment wiring that match this repository.
- Backend binds to Render's assigned port and responds to its configured health check.
- PostgreSQL schema setup uses the existing migration, and health output clearly indicates persistence readiness.
- Required Render environment variables and setup steps are documented without exposing secrets.
- Existing agent workflow and conversation semantics are unchanged.
