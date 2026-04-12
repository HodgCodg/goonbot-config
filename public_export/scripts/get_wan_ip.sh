#!/bin/bash
WAN_IP=$(curl -s --max-time 5 https://api.ipify.org?format=text)
echo "$WAN_IP"
echo "WAN IP updated: $WAN_IP at $(date)" >> /tmp/wan_ip.log
cat /tmp/wan_ip.log | tail -5
