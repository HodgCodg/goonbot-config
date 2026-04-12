#!/bin/bash
# Live Bandwidth Monitor - Shows real-time MBPS up/down

INTERFACE="ens18"

echo "Live Bandwidth Monitor (Ctrl+C to stop)"
echo "========================================"

while true; do
    # Get current traffic stats
    STATS=$(cat /proc/net/dev | grep "$INTERFACE")
    RX_BYTES=$(echo $STATS | awk '{print $2}')
    TX_BYTES=$(echo $STATS | awk '{print $10}')
    
    # Store previous values
    PREV_RX=${PREV_RX:-$RX_BYTES}
    PREV_TX=${PREV_TX:-$TX_BYTES}
    
    # Calculate differences
    RX_DIFF=$((RX_BYTES - PREV_RX))
    TX_DIFF=$((TX_BYTES - PREV_TX))
    
    # Convert to Mbps (bytes * 8 / 1000000)
    if command -v bc &>/dev/null; then
        RX_MBPS=$(echo "scale=2; $RX_DIFF * 8 / 1000000" | bc)
        TX_MBPS=$(echo "scale=2; $TX_DIFF * 8 / 1000000" | bc)
    else
        RX_MBPS=$((RX_DIFF * 8 / 1000000))
        TX_MBPS=$((TX_DIFF * 8 / 1000000))
    fi
    
    # Clear screen and display
    clear
    echo "========================================"
    echo "   LIVE BANDWIDTH - $INTERFACE"
    echo "========================================"
    printf "↓ Download: %12s Mbps\n" "$RX_MBPS"
    printf "↑ Upload:   %12s Mbps\n" "$TX_MBPS"
    echo "----------------------------------------"
    echo "Time: $(date '+%H:%M:%S')"
    
    # Update previous values
    PREV_RX=$RX_BYTES
    PREV_TX=$TX_BYTES
    
    sleep 1
done
