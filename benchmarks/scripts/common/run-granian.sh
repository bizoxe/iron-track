#!/usr/bin/env bash

echo "Increasing file descriptor limits (ulimit)..."
ulimit -n 65535

echo "Running Granian with 2 workers on cores 0 and 1..."

source .venv/bin/activate

taskset -c 0,1 granian src.app.main:app \
  --interface asgi \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2 \
  --loop uvloop \
  --backlog 2048 \
  --no-access-log \
  > /dev/null 2>&1 &
