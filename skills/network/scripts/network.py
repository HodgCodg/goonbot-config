#!/usr/bin/env python3
"""Network diagnostics.
Usage:
  network.py ping HOST          - Ping a host (3 packets)
  network.py dns HOST            - DNS lookup
  network.py port HOST PORT      - Check if a port is open
  network.py interfaces          - Show network interfaces
  network.py tailscale           - Tailscale status
  network.py connections         - Active connections summary
"""
import subprocess, sys, socket

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
    return r.stdout.strip() if r.returncode == 0 else f"ERROR: {r.stderr.strip()}"

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "ping":
        host = sys.argv[2] if len(sys.argv) > 2 else "8.8.8.8"
        print(run(f"ping -c 3 -W 2 {host}"))
    elif cmd == "dns":
        host = sys.argv[2] if len(sys.argv) > 2 else ""
        try:
            ips = socket.getaddrinfo(host, None)
            seen = set()
            for af, st, proto, cn, sa in ips:
                if sa[0] not in seen:
                    seen.add(sa[0])
                    print(f"{host} -> {sa[0]}")
        except Exception as e:
            print(f"DNS error: {e}")
    elif cmd == "port":
        host = sys.argv[2] if len(sys.argv) > 2 else ""
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 80
        try:
            s = socket.create_connection((host, port), timeout=3)
            s.close()
            print(f"{host}:{port} OPEN")
        except Exception as e:
            print(f"{host}:{port} CLOSED ({e})")
    elif cmd == "interfaces":
        print(run("ip -br addr"))
    elif cmd == "tailscale":
        print(run("tailscale status 2>&1"))
    elif cmd == "connections":
        print(run("ss -tuln | head -20"))
    else:
        print(f"Unknown: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()