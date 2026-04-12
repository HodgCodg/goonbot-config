#!/usr/bin/env python3
import sys, subprocess

def main():
    if len(sys.argv) < 2:
        print("Usage: weather.py 'City State'")
        sys.exit(1)
    city = " ".join(sys.argv[1:]).replace(" ", "+").replace(",", "")
    result = subprocess.run(["curl", "-s", f"wttr.in/{city}?format=3"], capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(result.stdout.strip())

if __name__ == "__main__":
    main()
