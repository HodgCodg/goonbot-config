#!/bin/bash
# System Monitor - BotVM Dashboard

WAN_IP=$(curl -s --max-time 3 https://api.ipify.org?format=text)
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "========================================"
echo "    BOTVM SYSTEM STATUS - $DATE"
echo "========================================"
echo "WAN IP: $WAN_IP"
echo "----------------------------------------"

# System stats
UPTIME=$(uptime -p)
LOAD=$(cat /proc/loadavg | awk '{print $1, $2, $3}')
MEM_USED=$(free | grep Mem | awk '{print $3}')
MEM_TOTAL=$(free | grep Mem | awk '{print $2}')
MEM_PCT=$((MEM_USED * 100 / MEM_TOTAL))
echo "Uptime:   $UPTIME"
echo "Load Avg: $LOAD"
echo "Memory:   ${MEM_USED}K/${MEM_TOTAL}K (${MEM_PCT}% used)"
echo "----------------------------------------"

# Network interfaces
echo "Network Interfaces:"
ip -br addr show | grep -v lo | while read line; do echo "  $line"; done
echo "----------------------------------------"

# Docker containers
echo "Docker Containers:"
docker ps --format "{{.Names}}\t{{.Status}}\t{{.State}}" 2>/dev/null || echo "  Docker not accessible"
echo "========================================"
