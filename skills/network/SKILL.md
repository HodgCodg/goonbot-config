---
name: network
description: Network diagnostics — ping, DNS, port check, interfaces, Tailscale.
metadata:
  openclaw:
    emoji: "🔌"
---
# Network

```bash
python3 {baseDir}/scripts/network.py ping HOST
python3 {baseDir}/scripts/network.py dns HOST
python3 {baseDir}/scripts/network.py port HOST PORT
python3 {baseDir}/scripts/network.py interfaces
python3 {baseDir}/scripts/network.py tailscale
python3 {baseDir}/scripts/network.py connections
```
