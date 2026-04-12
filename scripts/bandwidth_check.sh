#!/bin/bash
# One-shot Bandwidth Check - Shows current MBPS up/down

INTERFACE="ens18"

# Get initial stats
STATS=$(cat /proc/net/dev | grep "$INTERFACE")
RX_BYTES=$(echo $STATS | awk '{print $2}')
TX_BYTES=$(echo $STATS | awk '{print $10}')

sleep 1

# Get new stats
STATS=$(cat /proc/net/dev | grep "$INTERFACE")
NEW_RX=$(echo $STATS | awk '{print $2}')
NEW_TX=$(echo $STATS | awk '{print $10}')

# Calculate differences and convert to Mbps
RX_DIFF=$((NEW_RX - RX_BYTES))
TX_DIFF=$((NEW_TX - TX_BYTES))

if command -v bc &>/dev/null; then
    RX_MBPS=$(echo "scale=2; $RX_DIFF * 8 / 1000000" | bc)
    TX_MBPS=$(echo "scale=2; $TX_DIFF * 8 / 1000000" | bc)
else
    RX_MBPS=$((RX_DIFF * 8 / 1000000))
    TX_MBPS=$((TX_DIFF * 8 / 1000000))
fi

# Format output with leading zero if needed
[[ "$RX_MBPS" == .* ]] && RX_MBPS="0$RX_MBPS"
[[ "$TX_MBPS" == .* ]] && TX_MBPS="0$TX_MBPS"

echo "========================================"
echo "   BANDWIDTH CHECK - $INTERFACE"
echo "========================================"
printf "↓ Download: %s Mbps\n" "$RX_MBPS"
printf "↑ Upload:   %s Mbps\n" "$TX_MBPS"
echo "Time: $(date '+%H:%M:%S')"
echo "========================================"
