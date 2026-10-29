# QA runner: PyTest, Vitest, Newman, Playwright (+ Chromium), Bandit, pip-audit, ffmpeg for the demo videos.
# Build context is the repository root. Used via docker-compose.qa.yml (see qa.sh / qa.ps1).
FROM python:3.12-bookworm

# Node 22 copied from the official image (avoids a curl|bash installer).
COPY --from=node:22-bookworm /usr/local/bin/node /usr/local/bin/node
COPY --from=node:22-bookworm /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 CI=1
WORKDIR /repo

# Dependency layers first: editing a test does not reinstall everything.
COPY backend/requirements.txt backend/requirements.txt
COPY qa/requirements.txt qa/requirements.txt
RUN pip install -r backend/requirements.txt -r qa/requirements.txt

COPY frontend/package.json frontend/package-lock.json frontend/
RUN npm ci --prefix frontend

COPY qa/package.json qa/package-lock.json qa/
RUN npm ci --prefix qa && cd qa && npx playwright install --with-deps chromium

COPY . .
# The demo recorder imports `playwright`; reuse the QA copy instead of installing it twice.
RUN ln -s /repo/qa/node_modules /repo/demo/node_modules

CMD ["python", "qa/run.py", "--help"]
