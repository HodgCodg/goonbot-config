# Long-Term Memory Skill

## Description
Persistent memory storage for OpenClaw agents with recall, automatic storage of important information, and context compaction capabilities.

## Location
`/home/botvm/.openclaw/workspace/skills/longterm-memory/`

## Files
- `SKILL.md` - This documentation
- `scripts/memory.py` - Main memory operations CLI
- `data/memories.jsonl` - Append-only JSONL storage (one entry per line)

---

## Memory Entry Format

Each line in `memories.jsonl`:
```json
{
  "id": "uuid-short",
  "timestamp": "ISO8601-UTC",
  "type": "fact|auto|compact|summary|preference|event",
  "content": "the stored information",
  "tags": ["optional tags"],
  "priority": 1-5,
  "source": "user|agent"
}
```

### Types
| Type | Description |
|------|-------------|
| `fact` | General factual information |
| `preference` | User preferences, habits, rules |
| `auto` | Agent-auto-stored important info |
| `compact` | Context compaction summary |
| `summary` | Manual conversation/topic summary |
| `event` | Significant events or decisions |

### Priority Levels
- **5** - Critical, always recall (user identity, core preferences)
- **4** - High importance (work details, major facts)
- **3** - Medium importance (default)
- **2** - Low importance (minor details)
- **1** - Temporary/low value

---

## CLI Reference

### Store a Memory
```bash
# Basic store
python3 memory.py store "Zach prefers concise answers" --tags preferences --priority 4

# With type
python3 memory.py store "User works at NetSteady" --type fact --source user
```

### Auto-Store (Agent Use)
```bash
# Agent auto-stores important info without prompting
python3 memory.py auto "User mentioned they're working on project X"
```

### Recall / Search
```bash
# Search by query text
python3 memory.py recall "preferences" -n 5

# List recent memories
python3 memory.py list -n 10

# Filter by type
python3 memory.py recall --type preference -n 20

# Minimum priority filter
python3 memory.py recall --min-priority 4 -n 10
```

### Get Specific Entry
```bash
python3 memory.py get abc12345
```

### Context Compaction
```bash
# Agent compacts old context into LTM
python3 memory.py compact --summary "User discussed X, Y, Z in earlier conversation. Key point: A." --tags topic-x
```

### Status & Tags
```bash
python3 memory.py status
python3 memory.py tags
```

---

## Agent Behavior Guidelines

### When to Auto-Store
The agent should call `memory.py auto` when:

1. **Explicit preferences stated**
   - "I prefer X over Y"
   - "Always do Z"
   - "Don't bother me with W"

2. **Important personal facts emerge**
   - Work, school, location details
   - Relationships, family info
   - Hobbies, interests, habits

3. **User says "remember this" or similar**
   - Direct request to store something

4. **Significant events/decisions**
   - Major life changes mentioned
   - Important decisions made
   - Notable achievements or setbacks

5. **Recurring patterns observed**
   - User consistently does X
   - Regular schedule/routine noted

### When to Recall
Query memory when:
- User asks about something previously discussed
- Context seems incomplete and prior info might help
- User references "like before" or similar
- Starting a new session (optional: load recent high-priority memories)

### Context Compaction Strategy
When context is tight (~80% used):

1. **Identify old turns** that are less relevant to current task
2. **Summarize them** into compact form:
   - Who/what was discussed
   - Key decisions/outcomes
   - Important facts revealed
3. **Store via compaction:**
   ```bash
   python3 memory.py compact --summary "SUMMARY TEXT"
   ```
4. **Use the summary** in place of full old context
5. **This frees tokens** while preserving info in LTM

### Example Compaction Summary Format
```
[Topic] Brief description of what was discussed.
[Key Facts] 1-2 important facts revealed.
[Outcome] Any decisions or conclusions reached.
```

---

## Integration Notes

### Auto-Injection (Optional)
Recent high-priority memories could be auto-injected into context:
```bash
# Load last 5 priority-4+ memories at session start
python3 memory.py recall --min-priority 4 -n 5
```

### Tagging Strategy
Use tags for categorization:
- `preferences` - User preferences
- `work` - Work-related info
- `personal` - Personal life details
- `habits` - Regular behaviors
- `location` - Geographic info
- `relationships` - People in user's life
- `projects` - Ongoing projects

### Storage Limits
- JSONL is append-only and grows indefinitely
- Consider periodic cleanup of low-priority old entries
- Archive strategy: move priority-1 entries older than X days to backup

---

## Example Usage Session

```bash
# User states a preference
> I really prefer short, direct answers without fluff.

$ python3 memory.py auto "User prefers short, direct answers without fluff" --tags preferences --priority 4
[abc123] User prefers short, direct answers without f...

# Later, user asks about something
> What did we talk about last time?

$ python3 memory.py recall -n 5
[def456] 2026-04-06T19:30:00Z | auto|agent [preferences]
    User prefers short, direct answers without fluff
...
```

---

## Maintenance

### Backup
```bash
cp data/memories.jsonl data/memories.jsonl.backup.$(date +%Y%m%d)
```

### Cleanup Low-Priority Old Entries
```python
# Example: remove priority-1 entries older than 90 days
import json, datetime
from pathlib import Path

cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=90)
with open('data/memories.jsonl') as f:
    lines = f.readlines()
filtered = [l for l in lines if json.loads(l).get('priority', 3) > 1 or \
            datetime.datetime.fromisoformat(json.loads(l)['timestamp'].rstrip('Z')) > cutoff]
with open('data/memories.jsonl', 'w') as f:
    f.writelines(filtered)
```

---

## Version History
- **v1.0** - Initial release with store/recall/auto-store/compact
