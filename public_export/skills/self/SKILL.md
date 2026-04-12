---
name: self
description: GoonBot self-optimization — read/write workspace files.
metadata:
  openclaw:
    emoji: "⚙️"
---
# Self Edit

```bash
python3 {baseDir}/scripts/self_edit.py read <filepath>
python3 {baseDir}/scripts/self_edit.py write <filepath> <content>
python3 {baseDir}/scripts/self_edit.py append <filepath> <content>
python3 {baseDir}/scripts/self_edit.py list [dir]
python3 {baseDir}/scripts/self_edit.py backup <filepath>
```

All paths relative to `/home/botvm/.openclaw/workspace/`.
