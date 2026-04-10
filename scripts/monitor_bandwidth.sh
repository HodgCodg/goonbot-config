#!/bin/bash
# Simple bandwidth monitor using /proc/net/dev - no sudo needed

INTERFACE="ens18"  # BotVM's main interface

get_traffic() {
    local rx_bytes=$(grep "$INTERFACE" /proc/net/dev | awk '{print $2}')
    local tx_bytes=$(grep "$INTERFACE" /proc/net/dev | awk '{print $10}')
    echo "$rx_bytes $tx_bytes"
}

read RX1 TX1 <<< $(get_traffic)
sleep 1
read RX2 TX2 <<< $(get_traffic)

RX_DIFF=$((RX2 - RX1))
TX_DIFF=$((TX2 - TX1))

# Convert to MB/s (bytes * 8 / 1000000 for Mbps)
RX_MBPS=$(echo "scale=2; $RX_DIFF * 8 / 1000000" | bc 2>/dev/null || echo "N/A")
TX_MBPS=$(echo "scale=2; $TX_DIFF * 8 / 1000000" | bc 2>/dev/null || echo "N/A")

echo "=== BotVM ($INTERFACE) Bandwidth ==="
echo "Download: ${RX_MBPS} Mbps"
echo "Upload:   ${TX_MBPS} Mbps"
echo "Time: $(date '+%H:%M:%S')"
