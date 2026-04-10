# AGENTS.md
# Agent routing config.

---

## Standing Order: Request Triage

**Purpose:** Optimize VRAM and compute by routing each request to the appropriate execution tier before doing any work.

**Run triage on every non-trivial request** (skip only for greetings, single-word lookups, or pure conversation):

```bash
python3 /home/botvm/.openclaw/workspace/skills/triage/scripts/triage.py '<the user request>'
```

**Act on the result:**

| Tier | Score | Icon | Action |
|------|-------|------|--------|
| Tier 1 | ≥ 8 | 🔴 | Handle directly. Full context. Architect-level planning: Plan → Execute → Verify. |
| Tier 2 | 4–7 | 🟡 | Spawn a subagent with a Mission Brief. Verify result before replying. Escalate to T1 if it fails. |
| Tier 3 | 0–3 | 🟢 | Spawn a subagent with minimal context (task + 1 key fact). Trust result for reads. Escalate to T2 on error. |

**For Tier 2 or Tier 3: generate a Mission Brief before spawning the subagent:**
```bash
python3 /home/botvm/.openclaw/workspace/skills/triage/scripts/triage.py '<query>' --brief '<concrete task>' --context '<1-2 line context summary>' --json
```
Use the `mission_brief` field from the JSON output as the subagent's task string.

**Escalation ladder:**
- Tier 3 subagent fails or expresses uncertainty → escalate to Tier 2
- Tier 2 subagent fails twice → escalate to Tier 1 (handle directly)
- Tier 1 fails twice → alert user: "User intervention required"

**Final verification:** For Tier 2/3 tasks involving writes or system changes, always do a quick verification step after the subagent reports completion.

---

---

## Standing Order: Long-Term Task Management

**Authority:** You are authorized to read and write /home/botvm/.openclaw/workspace/TODO.md to manage an ongoing task queue. You may create, update, and complete tasks autonomously.

**When a user asks you to do something that will take time or multiple steps:**
1. Write the task to TODO.md under "## Active Tasks" using the standard format (next available TASK-XXX ID, status: pending)
2. Confirm to the user: "Added to queue as TASK-XXX. I'll work on it and report back."
3. Begin the task immediately if no higher-priority work is in progress

**When executing a task:**
- Always follow execute-verify-report: do the work, confirm it worked, write the result
- Update TODO.md status to "in-progress" before starting, "done" when finished
- Move completed tasks under "## Completed Tasks" when done
- Never mark a task done without verifying success

**When a user asks for status:**
- Read TODO.md and summarize active/pending/recently completed tasks
- Be concise — task ID, title, status, and one-line summary

**Escalation triggers (message the user immediately):**
- A task fails after two attempts
- A task requires credentials or permissions you don't have
- A task's scope is ambiguous and you need clarification before proceeding

**Boundaries:**
- Do not delete tasks — mark them cancelled instead
- Do not start a new task if one is already in-progress (finish or stall-reset first)
- Do not auto-install system packages or make destructive filesystem changes without asking

---

## Standing Order: Long-Term Memory

**Memory script:** `/home/botvm/.openclaw/workspace/skills/longterm-memory/scripts/memory.py`

**At the start of every session**, run:
```
python3 /home/botvm/.openclaw/workspace/skills/longterm-memory/scripts/memory.py recall --min-priority 4 -n 10
```
Read the output and use it to inform your behavior (preferences, facts, ongoing context).

**Auto-store when any of the following occur:**
- User states a preference ("I prefer...", "always do...", "don't...")
- User shares a personal fact (work, family, location, interests)
- User says "remember this" or similar
- A significant decision or event is made
- A recurring pattern is noticed

Use the right command:
```bash
# Preference (priority 5)
python3 memory.py store "<what to remember>" --type preference --tags preferences --priority 5

# Important fact (priority 4)
python3 memory.py store "<what to remember>" --type fact --tags <relevant,tags> --priority 4

# Auto-observed info (priority 3)
python3 memory.py auto "<what to remember>"
```

**When user asks what you remember**, recall and summarize:
```bash
python3 memory.py recall "<query>" -n 5
# or
python3 memory.py list -n 20
```

**Boundaries:**
- Do not store trivial one-off messages
- Do not store sensitive data (passwords, keys)
- Store concisely — one clear sentence per memory entry