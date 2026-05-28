#!/usr/bin/env bash
set -e
killall granian uvicorn 2>/dev/null || true

# The script must be run from the project root directory!
# Note: Granian optimization flags are not moved to variables and are edited directly in the launch command.
# ==========================================
# CONFIGURATION (EDIT BEFORE RUN)
# ==========================================
TEST_NAME="test-ping-with-logging-01"
TARGET_URL="http://127.0.0.1:8000/ping"
APP_IMPORT="src.app.main:app"
# Load generator parameters (wrk2)
RPS_LIMIT=1000
DURATION="30s"
THREADS=2
CONNECTIONS=10
LOAD_GEN_CPUS="6,7"
# Warm-up parameters
WARMUP_RPS=600
WARMUP_CONNECTIONS=6
WARMUP_DURATION="5s"
# Application server parameters
# Available options: "granian" or "uvicorn"
SERVER_TYPE="uvicorn"
HOST="127.0.0.1"
PORT="8000"
WORKERS=2
APP_CPUS="0,1"
# Directories
BASE_RESULTS_DIR="./results/${TEST_NAME}"
WRK_LOGS_DIR="${BASE_RESULTS_DIR}/wrk2-logs"
# ==========================================
mkdir -p "$BASE_RESULTS_DIR"
mkdir -p "$WRK_LOGS_DIR"

echo "[+] Preparing environment..."
ulimit -n 65535
source .venv/bin/activate

# --- APPLICATION SERVER RUN ---
echo "[+] Starting ${SERVER_TYPE} server on cores ${APP_CPUS}..."
if [ "$SERVER_TYPE" == "granian" ]; then
    taskset -c ${APP_CPUS} granian ${APP_IMPORT} --interface asgi --host ${HOST} --port ${PORT} \
        --workers ${WORKERS} --loop uvloop --backlog 1024 > /dev/null 2>&1 &
elif [ "$SERVER_TYPE" == "uvicorn" ]; then
    taskset -c ${APP_CPUS} uvicorn ${APP_IMPORT} \
        --host ${HOST} --port ${PORT} --workers ${WORKERS} \
        --loop uvloop --http httptools --no-access-log --log-level warning > /dev/null 2>&1 &
else
    echo "[-] Error: Unknown server type ${SERVER_TYPE}"; exit 1
fi

SERVER_PID=$!

echo "[+] Waiting for port ${PORT}..."
timeout 10s bash -c "until nc -z ${HOST} ${PORT}; do sleep 0.1; done" || (echo "[-] Server failed to start"; kill $SERVER_PID; exit 1)

# --- WARM-UP ---
echo "[+] Running warm-up (${WARMUP_DURATION})..."
taskset -c ${LOAD_GEN_CPUS} wrk2 \
    -t${THREADS} -c${WARMUP_CONNECTIONS} -d${WARMUP_DURATION} -R${WARMUP_RPS} \
    ${TARGET_URL} > /dev/null

echo "[+] Warm-up complete. Technical pause 15s..."
sleep 15

# --- MAIN TESTS ---
for i in {1..3}
do
    TIMESTAMP=$(date +"%d%m_%H%M")
    LOG_FILE="${WRK_LOGS_DIR}/run_${i}_${TIMESTAMP}.txt"

    echo "[+] Starting run #$i ($DURATION)..."
    taskset -c ${LOAD_GEN_CPUS} wrk2 \
        -t${THREADS} -c${CONNECTIONS} -d${DURATION} -R${RPS_LIMIT} \
        --latency ${TARGET_URL} > "${LOG_FILE}"

    echo "[+] Run #$i complete. Result in ${LOG_FILE}"
    echo "Technical pause 20s..."
    [ $i -lt 3 ] && sleep 20
done

echo "[+] Testing finished. Stopping server..."
kill $SERVER_PID 2>/dev/null || true
sleep 2
killall granian uvicorn 2>/dev/null || true

echo "--------------------------------------------------------"
echo "[+] All results saved in: ${WRK_LOGS_DIR}"