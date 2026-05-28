#!/usr/bin/env bash

echo "Increasing file descriptor limits (ulimit)..."
ulimit -n 65535

echo "Running Uvicorn with 2 workers on cores 0 and 1..."

source .venv/bin/activate

taskset -c 0,1 uvicorn src.app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2 \
  --loop uvloop \
  --http httptools \
  --no-access-log \
  --log-level warning \
  > /dev/null 2>&1 &
