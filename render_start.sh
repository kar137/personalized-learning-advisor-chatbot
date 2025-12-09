#!/usr/bin/env bash
set -euo pipefail

# render_start.sh
# 1. Start a lightweight Python HTTP server on $PORT immediately so Render's port scanner succeeds.
# 2. Launch Rasa on an internal port (RASA_INTERNAL_PORT) in the background.
# 3. The Python server proxies/forwards requests to Rasa once it's ready.

echo "=== render_start.sh ==="
echo "Current working directory: $(pwd)"
echo "Contents of /app:"
ls -la /app 2>/dev/null || echo "/app not found"

# Render-provided port; default to 10000 for local testing
: ${PORT:=10000}
RASA_INTERNAL_PORT=5005

echo "PORT=$PORT (Render-facing), RASA_INTERNAL_PORT=$RASA_INTERNAL_PORT"

# --- Write endpoints.yml if ACTIONS_URL is set ---
ENDPOINTS_TMP="/tmp/endpoints.yml"
ENDPOINTS_ARG=""
if [ -n "${ACTIONS_URL:-}" ] && [ "${ACTIONS_URL:-}" != "<not-set>" ]; then
  cat > "$ENDPOINTS_TMP" <<EOF
action_endpoint:
  url: "${ACTIONS_URL}"
EOF
  echo "Wrote $ENDPOINTS_TMP with action_endpoint -> ${ACTIONS_URL}"
  ENDPOINTS_ARG="--endpoints $ENDPOINTS_TMP"
else
  echo "ACTIONS_URL not set; no endpoints file written."
fi

# --- Model selection ---
MODEL_ARG=""
MODELS_DIR="/app/models"

echo "Looking for models in ${MODELS_DIR}..."
if [ -d "${MODELS_DIR}" ]; then
  echo "Contents of ${MODELS_DIR}:"
  ls -la "${MODELS_DIR}" 2>/dev/null || echo "Could not list models directory"
else
  echo "WARNING: Models directory ${MODELS_DIR} does not exist!"
fi

# Try to find and use a model
if [ -n "${MODEL_FILE:-}" ]; then
  echo "MODEL_FILE env var is set to: ${MODEL_FILE}"
  
  # Check various possible paths
  POSSIBLE_PATHS=(
    "${MODEL_FILE}"
    "${MODELS_DIR}/${MODEL_FILE}"
    "/app/${MODEL_FILE}"
    "${MODELS_DIR}/$(basename ${MODEL_FILE})"
  )
  
  for CANDIDATE in "${POSSIBLE_PATHS[@]}"; do
    echo "Checking: ${CANDIDATE}"
    if [ -f "${CANDIDATE}" ]; then
      MODEL_PATH="${CANDIDATE}"
      echo "Found model at: ${MODEL_PATH}"
      break
    fi
  done
  
  if [ -n "${MODEL_PATH:-}" ] && [ -f "${MODEL_PATH}" ]; then
    echo "Using MODEL_FILE -> ${MODEL_PATH}"
    MODEL_ARG="--model ${MODEL_PATH}"
  else
    echo "WARNING: MODEL_FILE='${MODEL_FILE}' not found in any expected location" >&2
  fi
fi

# Auto-detect: if no MODEL_ARG yet, find the latest .tar.gz in MODELS_DIR
if [ -z "${MODEL_ARG}" ] && [ -d "${MODELS_DIR}" ]; then
  echo "Auto-detecting model in ${MODELS_DIR}..."
  LATEST_MODEL=$(ls -t "${MODELS_DIR}"/*.tar.gz 2>/dev/null | head -n1 || true)
  if [ -n "${LATEST_MODEL}" ] && [ -f "${LATEST_MODEL}" ]; then
    echo "Auto-detected latest model -> ${LATEST_MODEL}"
    MODEL_ARG="--model ${LATEST_MODEL}"
  else
    echo "No .tar.gz models found in ${MODELS_DIR}"
  fi
fi

# Fallback: MODEL_URL download
if [ -z "${MODEL_ARG}" ] && [ -n "${MODEL_URL:-}" ] && [ "${MODEL_URL:-}" != "<not-set>" ]; then
  echo "Downloading model from MODEL_URL=${MODEL_URL}"
  MODEL_TMP="/tmp/model.tar.gz"
  curl -fsSL "${MODEL_URL}" -o "${MODEL_TMP}" || wget -qO "${MODEL_TMP}" "${MODEL_URL}" || true
  if [ -s "${MODEL_TMP}" ]; then
    MODEL_ARG="--model ${MODEL_TMP}"
    echo "Downloaded model to ${MODEL_TMP}"
  else
    echo "WARNING: Failed to download model" >&2
  fi
fi

# Final check
if [ -z "${MODEL_ARG}" ]; then
  echo "ERROR: No model found! Rasa will start without a model and won't respond to messages." >&2
fi

echo "Final MODEL_ARG=${MODEL_ARG}"
echo "Final ENDPOINTS_ARG=${ENDPOINTS_ARG}"

# --- Create the Python proxy/health server ---
cat > /tmp/proxy_server.py << 'PYEOF'
#!/usr/bin/env python3
"""
Lightweight HTTP server that:
- Binds to PORT immediately so Render's port scanner succeeds.
- Proxies all requests to Rasa on RASA_INTERNAL_PORT once Rasa is ready.
- Returns 503 with a friendly message while Rasa is still loading.
"""
import http.server
import urllib.request
import urllib.error
import os
import sys
import socket

PORT = int(os.environ.get("PORT", 10000))
RASA_PORT = int(os.environ.get("RASA_INTERNAL_PORT", 5005))
RASA_BASE = f"http://127.0.0.1:{RASA_PORT}"

def rasa_ready():
    """Check if Rasa is accepting connections."""
    try:
        with socket.create_connection(("127.0.0.1", RASA_PORT), timeout=1):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Quiet logs

    def do_proxy(self):
        if not rasa_ready():
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"loading","message":"Rasa is still loading, please retry in a few seconds."}')
            return

        url = f"{RASA_BASE}{self.path}"
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else None

        req = urllib.request.Request(url, data=body, method=self.command)
        for h, v in self.headers.items():
            if h.lower() not in ("host", "content-length"):
                req.add_header(h, v)
        if body:
            req.add_header("Content-Length", str(len(body)))

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                self.send_response(resp.status)
                for h, v in resp.getheaders():
                    if h.lower() not in ("transfer-encoding",):
                        self.send_header(h, v)
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for h, v in e.headers.items():
                if h.lower() not in ("transfer-encoding",):
                    self.send_header(h, v)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(f'{{"error":"{e}"}}'.encode())

    do_GET = do_proxy
    do_POST = do_proxy
    do_PUT = do_proxy
    do_DELETE = do_proxy
    do_OPTIONS = do_proxy
    do_HEAD = do_proxy

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), ProxyHandler)
    print(f"[proxy] Listening on 0.0.0.0:{PORT}, forwarding to Rasa at 127.0.0.1:{RASA_PORT}", flush=True)
    server.serve_forever()
PYEOF

echo "Starting proxy server on port ${PORT}..."
export RASA_INTERNAL_PORT
python3 /tmp/proxy_server.py &
PROXY_PID=$!
echo "Proxy server started (PID $PROXY_PID)"

# Give the proxy a moment to bind
sleep 1

# --- Start Rasa with monitoring ---
echo "Starting Rasa on internal port ${RASA_INTERNAL_PORT}..."
echo "Memory info before Rasa start:"
free -h 2>/dev/null || cat /proc/meminfo 2>/dev/null | head -5 || echo "Cannot get memory info"

# Set environment variables to help with TensorFlow on limited resources
export TF_CPP_MIN_LOG_LEVEL=2
export TF_FORCE_GPU_ALLOW_GROWTH=true
export CUDA_VISIBLE_DEVICES=""
export TF_NUM_INTEROP_THREADS=1
export TF_NUM_INTRAOP_THREADS=1

# Force Python to use unbuffered output
export PYTHONUNBUFFERED=1

# Start a background monitor to check if Rasa process is alive
(
  sleep 30
  while true; do
    if ! kill -0 $$ 2>/dev/null; then
      echo "[monitor] Parent process died, exiting monitor"
      exit 0
    fi
    
    # Check if Rasa is listening on its port
    if ss -lntp 2>/dev/null | grep -q ":${RASA_INTERNAL_PORT}"; then
      echo "[monitor] Rasa is listening on port ${RASA_INTERNAL_PORT}"
    else
      echo "[monitor] Rasa NOT yet listening on port ${RASA_INTERNAL_PORT}"
    fi
    
    # Print memory usage
    free -h 2>/dev/null | head -2 || true
    
    sleep 60
  done
) &

echo "Executing: rasa run --enable-api --cors '*' --port ${RASA_INTERNAL_PORT} ${MODEL_ARG} ${ENDPOINTS_ARG}"
exec rasa run --enable-api --cors "*" --port ${RASA_INTERNAL_PORT} ${MODEL_ARG} ${ENDPOINTS_ARG}
