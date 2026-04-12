# BotVM System Health Audit Report
**Date:** 2026-04-11 16:56 CDT
**Status:** ⚠️ WARNING (Disk Space)

## 1. Executive Summary
The system is generally healthy with low CPU and Memory utilization. However, the root partition is critically low on space (95% used), which requires immediate attention to prevent system instability.

## 2. Resource Utilization
- **Uptime:** 2 days, 1 hour, 5 minutes
- **CPU Load:** Very Low (0.15 0.10 0.09)
- **RAM:** 3.2Gi used / 15Gi total (~21% utilization)
- **GPU:** Idle (0% load, 11 MiB VRAM used)

## 3. Storage Analysis
- **Root Partition (/):** 
  - Total: 62G
  - Used: 55G
  - Available: 3.6G
  - **Utilization: 95%** 🔴 (CRITICAL)

## 4. Service Status
- **Docker Containers:**
  - `ollama`: Up 22 minutes ✅
  - `searxng`: Up 2 days ✅
  - `clawdbot`: Up 2 days (healthy) ✅
- **Critical Processes:**
  - `openclaw-gateway`: Running (PID 1878655)
  - `tailscaled`: Running (PID 1085)
  - `syncthing`: Running (PID 1146)

## 5. Network Configuration
- **Local IP:** 10.11.0.114 (ens18)
- **Tailscale IP:** 100.107.171.88
- **Interface Status:** All primary interfaces UP.

## 6. Recommendations
- **Urgent:** Perform a cleanup of the root partition. Check for large logs, cached packages (`apt clean`), or orphaned Docker volumes.
- **Monitoring:** Monitor disk growth to determine if the 62G allocation is sufficient for long-term operations.
