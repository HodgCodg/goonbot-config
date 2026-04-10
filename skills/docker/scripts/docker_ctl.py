#!/usr/bin/env python3
"""Docker container management.
Usage:
  docker_ctl.py ps              - List running containers
  docker_ctl.py logs NAME [-n N] - Last N lines of logs (default 20)
  docker_ctl.py restart NAME     - Restart a container
  docker_ctl.py stats            - Resource usage snapshot
  docker_ctl.py inspect NAME     - Detailed container info
"""
import subprocess, sys

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout.strip() if r.returncode == 0 else f"ERROR: {r.stderr.strip()}"

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "ps":
        print(run("sudo docker ps --format \"table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}\""  ))
    elif cmd == "logs":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        n = "20"
        if "-n" in sys.argv:
            idx = sys.argv.index("-n")
            n = sys.argv[idx+1] if idx+1 < len(sys.argv) else "20"
        print(run(f"sudo docker logs --tail {n} {name} 2>&1"))
    elif cmd == "restart":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        print(run(f"sudo docker restart {name}"))
    elif cmd == "stats":
        print(run("sudo docker stats --no-stream --format \"table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\""  ))
    elif cmd == "inspect":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        print(run(f"sudo docker inspect {name} --format \"Name:{{{{.Name}}}} Image:{{{{.Config.Image}}}} State:{{{{.State.Status}}}} Started:{{{{.State.StartedAt}}}} Restart:{{{{.RestartCount}}}}\""  ))
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()