#!/bin/bash
# Carmen OpenClaw — Render Bootstrap Script
# 1. Initialize workspace from staging area (first boot only)
# 2. Create openclaw.json from env vars (first boot only)
# 3. Start the OpenClaw Gateway

set -e

CONFIG_DIR="${OPENCLAW_STATE_DIR:-/data/.openclaw}"
CONFIG_FILE="$CONFIG_DIR/openclaw.json"
WORKSPACE="${OPENCLAW_WORKSPACE_DIR:-/data/workspace}"
STAGING="/carmen-workspace-staging"

echo "[carmen] === BOOTSTRAP STARTING ==="
mkdir -p "$CONFIG_DIR" "$WORKSPACE"

# ── 1. Initialize workspace from staging (first boot only) ──
if [ ! -f "$WORKSPACE/MEMORY.md" ] && [ -d "$STAGING" ]; then
    echo "[carmen] First boot — copying workspace from staging..."
    # Copy everything except Docker/infra files & .git
    cp -r "$STAGING"/* "$WORKSPACE/" 2>/dev/null || true
    rm -rf "$WORKSPACE/.git" "$WORKSPACE/Dockerfile" "$WORKSPACE/render.yaml" \
           "$WORKSPACE/bootstrap.sh" "$WORKSPACE/.dockerignore" "$WORKSPACE/RENDER_DEPLOY.md" 2>/dev/null || true
    echo "[carmen] Workspace initialized: $(du -sh $WORKSPACE | cut -f1)"
else
    echo "[carmen] Workspace already initialized at $WORKSPACE"
fi

# ── 2. Create config from env vars (first boot only) ──
if [ ! -f "$CONFIG_FILE" ]; then
    echo "[carmen] Creating initial openclaw.json..."
    cat > "$CONFIG_FILE" << 'CONFEOF'
{
  "gateway": {
    "mode": "local",
    "auth": {
      "mode": "token",
      "token": "${OPENCLAW_GATEWAY_TOKEN}"
    },
    "port": 8080,
    "bind": "lan",
    "controlUi": {
      "allowInsecureAuth": true
    }
  },
  "agents": {
    "defaults": {
      "workspace": "/data/workspace",
      "model": {
        "primary": "deepseek/deepseek-v4-pro"
      },
      "models": {
        "deepseek/deepseek-v4-pro": {},
        "deepseek/deepseek-v4-flash": { "alias": "DeepSeek" },
        "google/gemini-3.1-pro-preview": {},
        "google/gemini-2.5-pro": {},
        "google/gemini-2.0-flash-lite": {},
        "google/gemini-2.5-flash-lite": {},
        "qwen/qwen3.5-plus": { "alias": "Qwen" },
        "qwen/qwen3-max-2026-01-23": {},
        "qwen/qwen3-coder-next": {},
        "qwen/qwen3-coder-plus": {},
        "qwen/MiniMax-M2.5": {},
        "qwen/glm-5": {},
        "qwen/kimi-k2.5": {}
      }
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "${CARMEN_TELEGRAM_BOT_TOKEN}"
    }
  },
  "tools": {
    "profile": "coding",
    "web": {
      "search": {
        "provider": "gemini",
        "enabled": true
      }
    }
  },
  "plugins": {
    "entries": {
      "deepseek": { "enabled": true },
      "google": {
        "enabled": true,
        "config": {
          "webSearch": {
            "apiKey": "${GEMINI_API_KEY}"
          }
        }
      },
      "qwen": { "enabled": true }
    }
  }
}
CONFEOF

    # Substitute env vars
    for var in OPENCLAW_GATEWAY_TOKEN CARMEN_TELEGRAM_BOT_TOKEN GEMINI_API_KEY; do
        value="${!var}"
        if [ -n "$value" ]; then
            escaped_value=$(echo "$value" | sed 's/[\/&]/\\&/g')
            sed -i "s/\${$var}/$escaped_value/g" "$CONFIG_FILE"
        fi
    done
    echo "[carmen] Config created at $CONFIG_FILE"
else
    echo "[carmen] Config exists — preserving"
fi

# ── 3. Install workspace npm deps if needed ──
if [ -f "$WORKSPACE/patreon-db/package.json" ] && [ ! -d "$WORKSPACE/patreon-db/node_modules" ]; then
    echo "[carmen] Installing patreon-db npm deps..."
    cd "$WORKSPACE/patreon-db" && npm install 2>/dev/null || true
fi

if [ -f "$WORKSPACE/youtube-pipeline/package.json" ] && [ ! -d "$WORKSPACE/youtube-pipeline/node_modules" ]; then
    echo "[carmen] Installing youtube-pipeline npm deps..."
    cd "$WORKSPACE/youtube-pipeline" && npm install 2>/dev/null || true
fi

# ── 4. Fix legacy config if needed ──
echo "[carmen] Checking config validity..."
openclaw doctor --fix --yes 2>/dev/null || true

# ── 5. Start gateway ──
echo "[carmen] Starting OpenClaw Gateway on port ${OPENCLAW_GATEWAY_PORT:-8080}..."
exec openclaw gateway start
