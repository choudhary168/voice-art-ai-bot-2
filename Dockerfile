FROM node:22-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY alembic.ini ./alembic.ini
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

EXPOSE 10000
CMD ["sh", "-c", "if ! python -m alembic -c alembic.ini upgrade head; then echo 'WARNING: database migration failed; starting in degraded persistence mode'; fi; exec uvicorn backend.main:app --host 0.0.0.0 --port \"${PORT:-10000}\""]
