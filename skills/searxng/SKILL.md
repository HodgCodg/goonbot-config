---
name: searxng
description: Search the web via self-hosted SearXNG for current events, news, or anything needing up-to-date info.
metadata:
  openclaw:
    emoji: "🔍"
    requires:
      bins:
        - python3
---
# SearXNG Web Search

```bash
python3 {baseDir}/scripts/search.py "your query" -n 5
```

Options: -n COUNT (results, default 5), -c CATEGORY (general|news|images|videos|science|it)

Rules: Write specific 4-8 word queries with WHO/WHAT and WHEN. Summarize results in your own words - never paste raw output. If results miss, refine and retry.
