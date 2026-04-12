# Session Summary: 2026-04-09 to 2026-04-10
## Key Accomplishments
- **Dashboard Stability & UI**: 
    - Fixed "PFSense Router" title to "TXPFSenseRouter" in `static/index.html`.
    - Fixed a critical bug in `status-dashboard.py` where `uptime -p` was being incorrectly parsed as a datetime string, causing SSH cards to fail and show as offline.
- **Connectivity**: 
    - Resolved `BeloitOrangePiZero3` offline status. Discovered that the `orangepi` user was denying access; switched to the `ubuntu` user, which restored connectivity and metrics.
- **Verification**: Verified all systems (BotVM, PFSense, Proxmox nodes, Orange Pis, FarmPis) are now reporting metrics correctly on the dashboard.

## State of Infrastructure
- **BotVM**: Online, updated.
- **TXPFSenseRouter**: Online, bandwidth monitoring active and smoothed.
- **BeloitOrangePiZero3**: Online (via 'ubuntu' user).
- **FarmPi2**: Online.
- **Proxmox Nodes**: Online, but experiencing high memory pressure (audit pending).
- **Orange Pi 5**: Online.
