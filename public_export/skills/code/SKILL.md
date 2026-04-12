---
name: code
description: Read, write, run, and search code files in the workspace.
metadata:
  openclaw:
    emoji: "💻"
---
# Code

```bash
python3 {baseDir}/scripts/code.py read <filepath>
python3 {baseDir}/scripts/code.py write <filepath>  # pipe content via stdin
python3 {baseDir}/scripts/code.py run <filepath> [args]
python3 {baseDir}/scripts/code.py search <pattern> [dir]
python3 {baseDir}/scripts/code.py git <command>
python3 {baseDir}/scripts/code.py tree [dir]
```
