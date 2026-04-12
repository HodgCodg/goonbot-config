#!/usr/bin/env python3
"""Coding assistant tool.
Usage:
  code.py read <filepath>         - Read a source file
  code.py write <filepath>        - Write from stdin (pipe content)
  code.py run <filepath> [args]   - Execute a script
  code.py search <pattern> [dir]  - Grep for pattern in code files
  code.py git <command>           - Run git command in workspace
  code.py lint <filepath>         - Basic syntax check (Python)
  code.py tree [dir]              - Show directory tree
  code.py diff <file1> <file2>    - Diff two files
"""
import subprocess, sys, os

def run(cmd, cwd=None, timeout=30):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd)
    out = r.stdout.strip()
    err = r.stderr.strip()
    if r.returncode != 0 and err:
        return f"EXIT {r.returncode}: {err}"
    return out if out else err

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    
    if cmd == "read":
        path = sys.argv[2] if len(sys.argv) > 2 else ""
        if not os.path.exists(path):
            print(f"File not found: {path}")
            sys.exit(1)
        with open(path) as f:
            content = f.read()
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            print(f"{i:4d} | {line}")
    
    elif cmd == "write":
        path = sys.argv[2] if len(sys.argv) > 2 else ""
        content = sys.stdin.read() if not sys.stdin.isatty() else " ".join(sys.argv[3:])
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        print(f"Wrote {len(content)} bytes to {path}")
    
    elif cmd == "run":
        path = sys.argv[2] if len(sys.argv) > 2 else ""
        args = " ".join(sys.argv[3:])
        ext = os.path.splitext(path)[1]
        if ext == ".py":
            print(run(f"python3 {path} {args}", timeout=60))
        elif ext == ".sh":
            print(run(f"bash {path} {args}", timeout=60))
        elif ext == ".js":
            print(run(f"node {path} {args}", timeout=60))
        else:
            print(run(f"chmod +x {path} && ./{path} {args}", timeout=60))
    
    elif cmd == "search":
        pattern = sys.argv[2] if len(sys.argv) > 2 else ""
        directory = sys.argv[3] if len(sys.argv) > 3 else "."
        print(run(f"grep -rn --include=\"*.py\" --include=\"*.js\" --include=\"*.sh\" --include=\"*.md\" --include=\"*.yaml\" --include=\"*.json\" \"{pattern}\" {directory} | head -30"))
    
    elif cmd == "git":
        gitcmd = " ".join(sys.argv[2:])
        print(run(f"git {gitcmd}"))
    
    elif cmd == "lint":
        path = sys.argv[2] if len(sys.argv) > 2 else ""
        ext = os.path.splitext(path)[1]
        if ext == ".py":
            print(run(f"python3 -m py_compile {path} && echo \"Syntax OK: {path}\""))
        else:
            print(f"No linter for {ext} files")
    
    elif cmd == "tree":
        directory = sys.argv[2] if len(sys.argv) > 2 else "."
        print(run(f"find {directory} -maxdepth 3 -not -path \"*/.git/*\" -not -path \"*/__pycache__/*\" -not -path \"*/node_modules/*\" | head -50 | sort"))
    
    elif cmd == "diff":
        f1 = sys.argv[2] if len(sys.argv) > 2 else ""
        f2 = sys.argv[3] if len(sys.argv) > 3 else ""
        print(run(f"diff --color=never {f1} {f2}"))
    
    else:
        print(f"Unknown: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()