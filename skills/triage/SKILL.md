---
name: triage
description: Score a request for complexity and get tier routing decision (Tier 1/2/3 with Mission Brief).
metadata:
  openclaw:
    emoji: "⚖️"
---
# Triage

Scores an incoming request against five weighted vectors and returns the appropriate
execution tier, preferred model, context level, and routing advice.

**Basic score:**
```bash
python3 {baseDir}/scripts/triage.py '<query>'
```

**JSON output (for scripting):**
```bash
python3 {baseDir}/scripts/triage.py '<query>' --json
```

**With Mission Brief for subagent dispatch:**
```bash
python3 {baseDir}/scripts/triage.py '<query>' --brief '<task>' --context '<summary>'
```

**Tier reference:**

| Tier | Score | Model         | Action                              |
|------|-------|---------------|-------------------------------------|
| 🔴 1  | ≥ 8   | 31B OpenRouter | Handle directly, full context        |
| 🟡 2  | 4–7   | 26B OpenRouter | Spawn subagent, moderate context     |
| 🟢 3  | 0–3   | Local 27B      | Spawn subagent, minimal context      |

**Scoring vectors (weights):**
- `risk_ops` (+5): destructive or privileged operations
- `tool_depth` (+2/extra tool): multi-tool chains
- `ambiguity` (+3): vague or open-ended phrasing
- `orchestration` (+4): batch or multi-target scope
- `domain_shift` (+3/extra domain): cross-service spans
