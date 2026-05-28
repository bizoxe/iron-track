#!/usr/bin/env bash
set -e
killall wrk2 sar 2>/dev/null || true

# The script must be run from the project root directory!
# ==========================================
# CONFIGURATION (EDIT BEFORE RUN)
# ==========================================
# Test name (root folder name for results)
TEST_NAME="test-ping-with-logging-01"
# Target URL (endpoint for the test)
TARGET_URL="http://127.0.0.1:8000/ping"
# Parameters for the load generator (wrk2)
RPS_LIMIT=1000
DURATION="30s"
THREADS=2
CONNECTIONS=10
LOAD_GEN_CPUS="6,7"
# Warm-up parameters
WARMUP_RPS=600
WARMUP_CONNECTIONS=6
WARMUP_DURATION="5s"
# Directory for saving results
BASE_RESULTS_DIR="./results/${TEST_NAME}"
# sar parameters
SAR_TEMP_FILE="/dev/shm/sar_${TEST_NAME}.bin"
# Directories
SAR_METRICS_DIR="$BASE_RESULTS_DIR/sar-metrics"
SAR_DIR="${SAR_METRICS_DIR}/sar"
WRK_DIR="${SAR_METRICS_DIR}/wrk2"
REPORT_DIR="${SAR_METRICS_DIR}/reports"
# ==========================================

mkdir -p "$BASE_RESULTS_DIR"
mkdir -p "$SAR_METRICS_DIR" "$SAR_DIR" "$WRK_DIR" "$REPORT_DIR"

echo "[+] Starting test: ${TEST_NAME} targeting ${TARGET_URL}"
echo "[+] Preparing environment..."
ulimit -n 65535

# --- WARMUP ---
echo "[+] Running warm-up run (${WARMUP_DURATION})..."
taskset -c ${LOAD_GEN_CPUS} wrk2 \
    -t${THREADS} \
    -c${WARMUP_CONNECTIONS} \
    -d${WARMUP_DURATION} \
    -R${WARMUP_RPS} \
    ${TARGET_URL} > /dev/null

sleep 5

# --- MAIN TEST ---
echo "[+] Starting main measurements (1 run, ${DURATION})..."
sar -u ALL -P ALL -r -B -n DEV,TCP,ETCP -w -d 1 40 -o "$SAR_TEMP_FILE" > /dev/null &
SAR_PID=$!

sleep 1

taskset -c ${LOAD_GEN_CPUS} wrk2 \
    -t${THREADS} \
    -c${CONNECTIONS} \
    -d${DURATION} \
    -R${RPS_LIMIT} \
    --latency \
    ${TARGET_URL} > "${WRK_DIR}/wrk_report.txt"

wait $SAR_PID

BIN_DATA="${SAR_DIR}/system_profile.bin"
mv "$SAR_TEMP_FILE" "$BIN_DATA"

# --- REPORT GENERATION ---
echo "[+] Generating final analytics package in ${REPORT_DIR}..."
sar -f "$BIN_DATA" -u ALL -P ALL > "$REPORT_DIR/cpu.txt"
sar -f "$BIN_DATA" -n DEV,TCP,ETCP,IP > "$REPORT_DIR/network.txt"
sar -f "$BIN_DATA" -n SOCK > "$REPORT_DIR/sockets.txt"
sar -f "$BIN_DATA" -w -q > "$REPORT_DIR/system.txt"
sar -f "$BIN_DATA" -r -B > "$REPORT_DIR/memory.txt"
sar -f "$BIN_DATA" -d -p > "$REPORT_DIR/disk_io.txt"

echo "[+] wrk2 test results:"
cat "${WRK_DIR}/wrk_report.txt"

echo "[+] Summary of CPU usage (Average per CPU):"
sar -f "${SAR_DIR}/system_profile.bin" -u -P ALL | sed -n '3p; /Average/p'

echo "--------------------------------------------------------"
echo "[+] All reports successfully generated in: ${REPORT_DIR}"
echo "[+] Analysis complete."