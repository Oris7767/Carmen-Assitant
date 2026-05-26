# Carmen OpenClaw — Custom Dockerfile for Render
# Based on node:24-bookworm-slim with Python, ffmpeg, Playwright

FROM node:24-bookworm-slim

# ── System dependencies ──────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev \
    ffmpeg \
    build-essential \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# ── Python packages (for patreon-db data collection) ─────
RUN pip3 install --break-system-packages --no-cache-dir \
    pyswisseph==2.10.3.2 \
    yfinance \
    pandas \
    numpy

# ── Install OpenClaw Gateway ─────────────────────────────
RUN npm install -g openclaw@latest

# ── Install Playwright browsers (for X, Meta, Patreon) ──
RUN npx playwright install-deps chromium 2>/dev/null || true
RUN npx playwright install chromium 2>/dev/null || true

# ── Environment ──────────────────────────────────────────
ENV OPENCLAW_STATE_DIR=/data/.openclaw
ENV OPENCLAW_WORKSPACE_DIR=/data/workspace
ENV OPENCLAW_GATEWAY_PORT=8080

# ── Setup workspace dirs ─────────────────────────────────
RUN mkdir -p /data/workspace /data/.openclaw

# ── Install workspace npm deps (for poster scripts) ──────
WORKDIR /data/workspace
RUN npm init -y 2>/dev/null || true
RUN npm install playwright dotenv twitter-api-v2 2>/dev/null || true

# ── Stage workspace files (copied to /data on first boot) ─
COPY . /carmen-workspace-staging

# ── Copy bootstrap script ────────────────────────────────
COPY bootstrap.sh /usr/local/bin/carmen-bootstrap
RUN chmod +x /usr/local/bin/carmen-bootstrap

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["/usr/local/bin/carmen-bootstrap"]
