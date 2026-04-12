#!/usr/bin/env python3
"""SSH exec skill - run commands on remote hosts via the SSH HTTP API."""
import sys, json, urllib.request, argparse

SSH_API_URL = "http://127.0.0.1:7722"

def ssh_exec(host, command, timeout=120):
    payload = json.dumps({"alias": host, "command": command}).encode()
    req = urllib.request.Request(
        f"{SSH_API_URL}/exec",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"SSH API error: {e}", file=sys.stderr)
        sys.exit(1)
    
    exit_code = data.get("exit_code", -1)
    stdout = data.get("stdout", "").strip()
    stderr = data.get("stderr", "").strip()
    
    if stdout:
        print(stdout)
    if stderr:
        print(f"STDERR: {stderr}", file=sys.stderr)
    if exit_code != 0:
        print(f"[exit code: {exit_code}]", file=sys.stderr)
    
    sys.exit(0 if exit_code == 0 else 1)

def list_hosts():
    try:
        req = urllib.request.Request(f"{SSH_API_URL}/hosts")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        for name, info in data.items():
            desc = info.get("description", "")
            print(f"  {name}: {desc}")
    except Exception as e:
        print(f"Error listing hosts: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SSH commands on remote hosts")
    parser.add_argument("command", nargs="?", help="Command to run")
    parser.add_argument("-H", "--host", default="botvm", help="Host alias (default: botvm)")
    parser.add_argument("-t", "--timeout", type=int, default=120, help="Timeout in seconds")
    parser.add_argument("--list-hosts", action="store_true", help="List available hosts")
    args = parser.parse_args()
    
    if args.list_hosts:
        list_hosts()
    elif args.command:
        ssh_exec(args.host, args.command, args.timeout)
    else:
        parser.print_help()
