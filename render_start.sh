#!/usr/bin/env bash
set -euo pipefail

# render_start.sh
# If ACTIONS_URL is set, write endpoints.yml pointing action_endpoint to it.
# Then start Rasa using the PORT provided by Render (environment variable $PORT).

echo "Preparing endpoints.yml from ACTIONS_URL=${ACTIONS_URL:-<not-set>}"

if [ -n "${ACTIONS_URL:-}" ] && [ "${ACTIONS_URL:-}" != "<not-set>" ]; then
  cat > endpoints.yml <<EOF
action_endpoint:
  url: "${ACTIONS_URL}"
EOF
  echo "Wrote endpoints.yml with action_endpoint -> ${ACTIONS_URL}"
else
  echo "ACTIONS_URL not set; leaving existing endpoints.yml (if any) unchanged."
fi

# Ensure PORT is set by Render; default to 5005 for local fallback
: ${PORT:=5005}

echo "Starting Rasa on port ${PORT}"
exec rasa run --enable-api --cors "*" --port ${PORT}
