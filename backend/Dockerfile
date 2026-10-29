# Flask API. Build context is the repository root:  docker build -f backend/Dockerfile .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first so code edits do not invalidate this layer.
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .

RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app

EXPOSE 5000

# gunicorn: many worker processes with few threads each. Python code is CPU-bound and the GIL lets one process use one core,
# so capacity scales with processes (12 x 2 gave p95 30 ms at 500 sessions; 4 x 8 gave 740 ms on the same machine).
# Tune with WEB_CONCURRENCY / GUNICORN_THREADS. --worker-tmp-dir keeps gunicorn's heartbeat file off the slow overlay filesystem.
ENV WEB_CONCURRENCY=12 GUNICORN_THREADS=2
CMD ["sh", "-c", "exec gunicorn -w $WEB_CONCURRENCY -k gthread --threads $GUNICORN_THREADS --backlog 2048 --graceful-timeout 10 --worker-tmp-dir /dev/shm -b 0.0.0.0:5000 'app:create_app()'"]

HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=12 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/v1/health', timeout=2)"
