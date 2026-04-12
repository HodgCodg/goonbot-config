#!/bin/bash
# Disk usage monitor for BotVM
USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$USAGE" -gt 92 ]; then
    # Use the openclaw gateway to send a message to the user.
    # Since I don't have the specific chat_id here, I'll use the message tool 
    # via a wrapper or assume the system has a way to notify.
    # Actually, the best way to trigger a notification in OpenClaw from a cron
    # is to write to a specific log or use a provided notification script.
    # But the user asked ME to do it. I can create a script that the 
    # openclaw gateway can run, or use the openclaw cli if available.
    
    # Given the 'openclaw' cli had a build error, I will use a simple 
    # echo to a file that I can check, or try to find the internal 
    # notification mechanism.
    
    # Better yet, I'll create a script that uses the `message` tool 
    # by calling the gateway API if possible, or simply logging it.
    # Actually, the most reliable way is to use the provided `openclaw cron` 
    # if it works, but the cli is broken.
    
    # Let's try to use a simple curl to the gateway's internal API if known,
    # but I don't have the token.
    
    # Alternative: The user wants ME to check. I can't "wake up" at 9am 
    # unless I have a cron job.
    
    # I will create a script that checks the usage and if it's > 92%,
    # it will create a "critical" file in the workspace that my heartbeat
    # or next session will definitely see.
    
    echo "CRITICAL: Disk usage is at ${USAGE}%" > /home/botvm/.openclaw/workspace/DISK_ALERT.txt
fi
