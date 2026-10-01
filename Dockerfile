# Stage 1 — build the React bundle.
FROM node:20-alpine AS webbuild
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# Stage 2 — runtime: API + the built bundle on one origin.
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=production \
    HOST=0.0.0.0 \
    PORT=8000 \
    DATA_DIR=/data

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=webbuild /web/dist ./frontend/dist

# Only used by the SQLite fallback (DATABASE_URL unset). When DATABASE_URL
# points at Neon/Postgres nothing important is written here, so Render's
# ephemeral free-tier filesystem is fine and no persistent disk is needed.
RUN mkdir -p /data
VOLUME ["/data"]
EXPOSE 8000

# Healthcheck used by the orchestrator; /api/health also runs migrations+seed on boot.
# start-period covers the first boot against an EMPTY remote database: it runs
# every migration and seeds the whole question bank over the network before the
# API answers. Subsequent boots only re-check content and are much faster.
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=4).status==200 else 1)"

CMD ["python", "backend/run.py"]
