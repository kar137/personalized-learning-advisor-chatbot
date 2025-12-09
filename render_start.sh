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
exec rasa run --enable-api --cors "*" --port ${PORT} $ENDPOINTS_ARG
