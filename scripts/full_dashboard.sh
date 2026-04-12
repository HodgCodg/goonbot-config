#!/bin/bash
# Full System Dashboard - BotVM + TxServerArm

WAN_IP=$(curl -s --max-time 3 https://api.ipify.org?format=text)
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "========================================"
echo "    FULL SYSTEM DASHBOARD - $DATE"
echo "========================================"
echo "WAN IP: $WAN_IP"
echo "----------------------------------------"

# === BOTVM SECTION ===
echo "=== BOTVM (10.11.0.114) ==="
UPTIME=$(uptime -p)
LOAD=$(cat /proc/loadavg | awk '{print $1, $2, $3}')
MEM_USED=$(free | grep Mem | awk '{print $3}')
MEM_TOTAL=$(free | grep Mem | awk '{print $2}')
MEM_PCT=$((MEM_USED * 100 / MEM_TOTAL))
echo "Uptime:   $UPTIME"
echo "Load Avg: $LOAD"
echo "Memory:   ${MEM_USED}K/${MEM_TOTAL}K (${MEM_PCT}% used)"
echo "----------------------------------------"

# Docker containers on BotVM
echo "Docker Containers (BotVM):"
docker ps --format "  {{.Names}}\t{{.Status}}\t{{.State}}" 2>/dev/null || echo "  Docker not accessible"
echo "----------------------------------------"

# === TXSERVERARM SECTION via Python script ===
echo "=== TXSERVERARM (10.11.0.173) ==="
python3 /home/botvm/.openclaw/workspace/scripts/txserverarm_stats.py
echo "----------------------------------------"

# === BANDWIDTH SECTION ===
echo "=== BANDWIDTH MONITORING ==="
INTERFACE="ens18"
STATS=$(cat /proc/net/dev | grep "$INTERFACE")
RX_BYTES=$(echo $STATS | awk '{print $2}')
TX_BYTES=$(echo $STATS | awk '{print $10}')
sleep 1
STATS=$(cat /proc/net/dev | grep "$INTERFACE")
NEW_RX=$(echo $STATS | awk '{print $2}')
NEW_TX=$(echo $STATS | awk '{print $10}')
RX_DIFF=$((NEW_RX - RX_BYTES))
TX_DIFF=$((NEW_TX - TX_BYTES))
echo "BotVM Traffic (last 1s): ${RX_DIFF} bytes in, ${TX_DIFF} bytes out"
echo "========================================"
