#!/usr/bin/env bash
set -euo pipefail

# render_start.sh
# If ACTIONS_URL is set, write endpoints.yml pointing action_endpoint to it.
# Then start Rasa using the PORT provided by Render (environment variable $PORT).

echo "Preparing endpoints.yml from ACTIONS_URL=${ACTIONS_URL:-<not-set>}"

# Write endpoints to a temp file (tmp is writable for non-root users in many images)
ENDPOINTS_TMP="/tmp/endpoints.yml"

if [ -n "${ACTIONS_URL:-}" ] && [ "${ACTIONS_URL:-}" != "<not-set>" ]; then
  cat > "$ENDPOINTS_TMP" <<EOF
action_endpoint:
  url: "${ACTIONS_URL}"
EOF
  echo "Wrote $ENDPOINTS_TMP with action_endpoint -> ${ACTIONS_URL}"
  ENDPOINTS_ARG="--endpoints $ENDPOINTS_TMP"
else
  echo "ACTIONS_URL not set; will not write endpoints file."
  ENDPOINTS_ARG=""
fi

# Ensure PORT is set by Render; default to 5005 for local fallback
: ${PORT:=5005}

echo "Starting Rasa on port ${PORT}"
# MODEL selection logic:
# - If MODEL_FILE env var is set and exists under /app/models, use it.
# - Else if MODEL_URL is set, the script will attempt to download it (kept for backward compatibility).
MODEL_ARG=""
MODELS_DIR="/app/models"

if [ -n "${MODEL_FILE:-}" ]; then
  # Allow both full paths and filenames
  if [ -f "${MODEL_FILE}" ]; then
    MODEL_PATH="${MODEL_FILE}"
  else
    MODEL_PATH="${MODELS_DIR}/${MODEL_FILE}"
  fi
  if [ -f "${MODEL_PATH}" ]; then
    echo "Using explicit MODEL_FILE -> ${MODEL_PATH}"
    # Quick integrity check: list tar contents and ensure expected resources exist
    set +e
    if tar -tzf "${MODEL_PATH}" >/tmp/model_contents.txt 2>/tmp/model_contents.err; then
      echo "Model archive contents (first 40 lines):"
      head -n 40 /tmp/model_contents.txt || true
      if grep -E "train_LexicalSyntacticFeaturizer.*/feature_to_idx_dict.pkl" /tmp/model_contents.txt >/dev/null 2>&1; then
        echo "Found feature_to_idx_dict.pkl for LexicalSyntacticFeaturizer inside archive."
      else
        echo "WARNING: feature_to_idx_dict.pkl not found inside the model archive. This may indicate an incompatible or incomplete model." >&2
      fi
    else
      echo "Failed to list model archive contents. stderr:" >&2
      sed -n '1,200p' /tmp/model_contents.err || true
    fi
    set -euo pipefail
    MODEL_ARG="--model ${MODEL_PATH}"
  else
    echo "MODEL_FILE was set to '${MODEL_FILE}' but file not found at ${MODEL_PATH}." >&2
  fi
fi

# Backwards-compatible: support MODEL_URL if MODEL_ARG not already set
if [ -z "${MODEL_ARG}" ] && [ -n "${MODEL_URL:-}" ] && [ "${MODEL_URL:-}" != "<not-set>" ]; then
  echo "MODEL_URL provided; attempting to download model from ${MODEL_URL}"
  MODEL_TMP="/tmp/model.tar.gz"
  set +e
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "${MODEL_URL}" -o "${MODEL_TMP}" || true
  fi
  if [ ! -s "${MODEL_TMP}" ] && command -v wget >/dev/null 2>&1; then
    wget -qO "${MODEL_TMP}" "${MODEL_URL}" || true
  fi
  set -euo pipefail
  if [ -s "${MODEL_TMP}" ]; then
    echo "Downloaded model to ${MODEL_TMP}"
    MODEL_ARG="--model ${MODEL_TMP}"
  else
    echo "Failed to download model from MODEL_URL=${MODEL_URL}" >&2
  fi
fi

echo "Starting rasa with args: --port ${PORT} ${MODEL_ARG} ${ENDPOINTS_ARG}"
echo "-- Startup diagnostics --"
echo "Environment summary:"
env | sed -n '1,200p' || true

echo "Rasa version:" 
if command -v rasa >/dev/null 2>&1; then
  rasa --version || true
else
  echo "rasa command not found"
fi

echo "Process list:"
ps aux || true

echo "Network listeners (ss/netstat):"
ss -lntp 2>/dev/null || netstat -tuln 2>/dev/null || true

echo "-- End diagnostics, starting Rasa now --"
exec rasa run --enable-api --cors "*" --port ${PORT} ${MODEL_ARG} ${ENDPOINTS_ARG}
