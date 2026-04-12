#!/usr/bin/env python3
"""Web fetch skill - fetch any URL and return content as markdown using Lightpanda."""
import sys, subprocess, argparse, urllib.parse

def fetch(url, wait_ms=3000, strip="full"):
    """Fetch a URL and return rendered markdown content."""
    cmd = ["lightpanda", "fetch", "--dump", "markdown",
           "--strip-mode", strip, "--wait-ms", str(wait_ms), url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0 and result.stderr:
            print(f"Error: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
        print(result.stdout)
    except subprocess.TimeoutExpired:
        print("Error: fetch timed out after 30s", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: lightpanda not found. Install at /usr/local/bin/lightpanda", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch a URL and return markdown content")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--wait", type=int, default=3000, help="Wait ms for JS (default: 3000)")
    parser.add_argument("--strip", default="full", help="Strip mode: full, js, css, ui (default: full)")
    args = parser.parse_args()
    fetch(args.url, args.wait, args.strip)

