#!/usr/bin/env python3
import sys, json, urllib.request, urllib.parse

SEARXNG_URL = "http://127.0.0.1:8888"

def search(query, count=5, category="general"):
    params = urllib.parse.urlencode({"q": query, "format": "json", "categories": category})
    url = f"{SEARXNG_URL}/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "OpenClaw-SearXNG-Skill/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    results = data.get("results", [])[:count]
    if not results:
        print("No results found.")
        return
    for i, r in enumerate(results, 1):
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = r.get("content", "No description")
        engines = ", ".join(r.get("engines", []))
        score = r.get("score", 0)
        print(f"{i}. {title}")
        print(f"   URL: {url}")
        print(f"   {snippet}")
        print(f"   Engines: {engines} | Score: {score:.2f}")
        print()

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("query", nargs="+")
    p.add_argument("-n", "--count", type=int, default=5)
    p.add_argument("-c", "--category", default="general")
    args = p.parse_args()
    search(" ".join(args.query), args.count, args.category)
