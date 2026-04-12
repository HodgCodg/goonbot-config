# MemPalace — Long-Term Memory

Semantic memory system. 37+ drawers indexed. No API key needed.

## Search
```bash
python3 -m mempalace search "your query" --results 5
python3 -m mempalace search "topic" --wing goonbot --room tasks
```

## Wake-up context (session start)
```bash
python3 -m mempalace wake-up
```

## Check status
```bash
python3 -m mempalace status
```

## Rooms: identity, tools, config, tasks, skills, user, memory, general

## Re-mine after compaction
```bash
rsync -av --include="*.md" --include="*.txt" --include="*.json" \
  --exclude="*.py" --exclude="*.html" --exclude="*.js" \
  --exclude="__pycache__/" --exclude="*.jsonl" \
  /home/botvm/.openclaw/workspace/ /tmp/mempalace_staging/ && \
  python3 -m mempalace mine /tmp/mempalace_staging --agent goonbot
```
