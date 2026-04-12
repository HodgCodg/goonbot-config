#!/usr/bin/env python3
"""System health snapshot."""
import subprocess, sys

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    return r.stdout.strip()

def main():
    full = "--full" in sys.argv
    print("=== System Health ===")
    print("Uptime:", run("uptime -p"))
    print("Load:", run("cat /proc/loadavg"))
    print("CPU:", run("top -bn1 | grep Cpu | head -1"))
    print("RAM:", run("free -h | grep Mem"))
    print("Disk:", run("df -h / | tail -1"))
    gpu = run("nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader 2>/dev/null")
    if gpu: print("GPU:", gpu)
    else: print("GPU: n/a")
    temps = run("sensors 2>/dev/null | grep -E \"Core|Package\" | head -4")
    if temps: print("Temps:", temps)
    docker = run("sudo docker ps --format \"{{.Names}}: {{.Status}}\" 2>/dev/null")
    if docker: print("Docker:", docker)
    if full:
        print("\n=== Top 5 (CPU) ===")
        print(run("ps aux --sort=-%cpu | head -6"))
        print("\n=== Mounts ===")
        print(run("df -h"))
        print("\n=== Network ===")
        print(run("ip -br addr"))

if __name__ == "__main__":
    main()