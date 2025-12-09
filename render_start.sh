#!/usr/bin/env bash
set -euo pipefail

# render_start.sh
# 1. Start a lightweight Python HTTP server on $PORT immediately so Render's port scanner succeeds.
# 2. Launch Rasa on an internal port (RASA_INTERNAL_PORT) in the background.
# 3. The Python server proxies/forwards requests to Rasa once it's ready.

echo "=== render_start.sh ==="

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
MODELS_DIR="/models"

if [ -n "${MODEL_FILE:-}" ]; then
  if [ -f "${MODEL_FILE}" ]; then
    MODEL_PATH="${MODEL_FILE}"
  else
    MODEL_PATH="${MODELS_DIR}/${MODEL_FILE}"
  fi
  if [ -f "${MODEL_PATH}" ]; then
    echo "Using MODEL_FILE -> ${MODEL_PATH}"
    MODEL_ARG="--model ${MODEL_PATH}"
  else
    echo "WARNING: MODEL_FILE set but not found at ${MODEL_PATH}" >&2
  fi
fi

# Fallback: MODEL_URL download
if [ -z "${MODEL_ARG}" ] && [ -n "${MODEL_URL:-}" ] && [ "${MODEL_URL:-}" != "<not-set>" ]; then
  echo "Downloading model from MODEL_URL=${MODEL_URL}"
  MODEL_TMP="/tmp/model.tar.gz"
  curl -fsSL "${MODEL_URL}" -o "${MODEL_TMP}" || wget -qO "${MODEL_TMP}" "${MODEL_URL}" || true
  if [ -s "${MODEL_TMP}" ]; then
    MODEL_ARG="--model ${MODEL_TMP}"
  else
    echo "WARNING: Failed to download model" >&2
  fi
fi

echo "MODEL_ARG=${MODEL_ARG}"
echo "ENDPOINTS_ARG=${ENDPOINTS_ARG}"

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

# --- Start Rasa in foreground (so container stays alive) ---
echo "Starting Rasa on internal port ${RASA_INTERNAL_PORT}..."
exec rasa run --enable-api --cors "*" --port ${RASA_INTERNAL_PORT} ${MODEL_ARG} ${ENDPOINTS_ARG}
