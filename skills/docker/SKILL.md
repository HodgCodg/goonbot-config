---
name: docker
description: Docker container management — list, logs, restart, stats.
metadata:
  openclaw:
    emoji: "🐳"
---
# Docker

```bash
python3 {baseDir}/scripts/docker_ctl.py ps
python3 {baseDir}/scripts/docker_ctl.py logs NAME [-n N]
python3 {baseDir}/scripts/docker_ctl.py restart NAME
python3 {baseDir}/scripts/docker_ctl.py stats
python3 {baseDir}/scripts/docker_ctl.py inspect NAME
```
