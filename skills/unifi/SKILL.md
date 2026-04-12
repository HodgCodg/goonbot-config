---
name: unifi
description: UniFi network controller at 10.11.0.173 — clients, devices, block/unblock.
metadata:
  openclaw:
    emoji: "📡"
---
# UniFi

```bash
python3 {baseDir}/scripts/unifi.py clients
python3 {baseDir}/scripts/unifi.py devices
python3 {baseDir}/scripts/unifi.py client NAME_OR_MAC
python3 {baseDir}/scripts/unifi.py block MAC
python3 {baseDir}/scripts/unifi.py unblock MAC
```
