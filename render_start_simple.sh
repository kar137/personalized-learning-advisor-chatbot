#!/bin/bash
set -e

echo "=== Simple Rasa Startup Script ==="

# PORT is set by Render (default 10000)
PORT=${PORT:-5005}

# ACTIONS_URL must be set by environment variable
ACTIONS_URL=${ACTIONS_URL:-"https://personalized-learning-advisor-chatbot-e6wd.onrender.com/webhook"}

echo "PORT=$PORT"
echo "ACTIONS_URL=$ACTIONS_URL"

# Write endpoints.yml dynamically
cat > /tmp/endpoints.yml << EOF
action_endpoint:
  url: ${ACTIONS_URL}
EOF

echo "Created /tmp/endpoints.yml with action_endpoint -> $ACTIONS_URL"

# Find the model file
MODELS_DIR="/app/models"
MODEL_FILE=${MODEL_FILE:-""}

if [ -z "$MODEL_FILE" ]; then
  # Auto-detect latest model
  LATEST_MODEL=$(ls -t ${MODELS_DIR}/*.tar.gz 2>/dev/null | head -1)
  if [ -n "$LATEST_MODEL" ]; then
    MODEL_FILE="$LATEST_MODEL"
    echo "Auto-detected model: $MODEL_FILE"
  fi
else
  # Check if MODEL_FILE is relative or absolute
  if [ ! -f "$MODEL_FILE" ]; then
    MODEL_FILE="${MODELS_DIR}/${MODEL_FILE}"
  fi
fi

if [ ! -f "$MODEL_FILE" ]; then
  echo "ERROR: No model file found!"
  ls -la ${MODELS_DIR}
  exit 1
fi

echo "Using model: $MODEL_FILE"

# TensorFlow optimizations
export TF_CPP_MIN_LOG_LEVEL=2
export CUDA_VISIBLE_DEVICES=""
export TF_NUM_INTEROP_THREADS=1
export TF_NUM_INTRAOP_THREADS=1
export PYTHONUNBUFFERED=1

echo "Starting Rasa on port $PORT..."
echo "This may take several minutes on limited CPU..."

# Start Rasa directly on the Render port
exec rasa run \
  --enable-api \
  --cors "*" \
  --port $PORT \
  --model "$MODEL_FILE" \
  --endpoints /tmp/endpoints.yml
