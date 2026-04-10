#!/usr/bin/env python3
"""GoonBot self-optimization tool.
Usage:
  self_edit.py read <filepath>           - Read a workspace file
  self_edit.py write <filepath> <content> - Write content to a workspace file
  self_edit.py list [dir]                - List workspace files
  self_edit.py append <filepath> <content> - Append to a file
  self_edit.py backup <filepath>         - Backup before editing

All paths are relative to /home/botvm/.openclaw/workspace/
"""
import sys, os, shutil, datetime

WORKSPACE = "/home/botvm/.openclaw/workspace"

def safe_path(rel):
    full = os.path.normpath(os.path.join(WORKSPACE, rel))
    if not full.startswith(WORKSPACE):
        print("ERROR: Path escapes workspace", file=sys.stderr)
        sys.exit(1)
    return full

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "read":
        if len(sys.argv) < 3:
            print("Usage: self_edit.py read <filepath>")
            sys.exit(1)
        path = safe_path(sys.argv[2])
        if not os.path.exists(path):
            print(f"ERROR: {sys.argv[2]} not found")
            sys.exit(1)
        with open(path) as f:
            print(f.read())

    elif cmd == "write":
        if len(sys.argv) < 4:
            print("Usage: self_edit.py write <filepath> <content>")
            sys.exit(1)
        path = safe_path(sys.argv[2])
        content = sys.argv[3]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        print(f"OK: wrote {len(content)} bytes to {sys.argv[2]}")

    elif cmd == "list":
        target = WORKSPACE if len(sys.argv) < 3 else safe_path(sys.argv[2])
        for item in sorted(os.listdir(target)):
            full = os.path.join(target, item)
            kind = "dir" if os.path.isdir(full) else "file"
            size = str(os.path.getsize(full)) if os.path.isfile(full) else ""
            print(f"  {kind:4s}  {size:>6s}  {item}")

    elif cmd == "append":
        if len(sys.argv) < 4:
            print("Usage: self_edit.py append <filepath> <content>")
            sys.exit(1)
        path = safe_path(sys.argv[2])
        with open(path, 'a') as f:
            f.write(sys.argv[3])
        print(f"OK: appended to {sys.argv[2]}")

    elif cmd == "backup":
        if len(sys.argv) < 3:
            print("Usage: self_edit.py backup <filepath>")
            sys.exit(1)
        path = safe_path(sys.argv[2])
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = f"{path}.bak.{ts}"
        shutil.copy2(path, bak)
        print(f"OK: backed up to {os.path.basename(bak)}")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
