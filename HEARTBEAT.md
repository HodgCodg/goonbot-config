# HEARTBEAT — GoonBot Autonomous Task Runner
# Fires every 30 minutes.

## STEP 1 — Get the task list
Call exec immediately with command: cat /home/botvm/.openclaw/workspace/TODO.md

Do NOT use the `read` tool. Do NOT narrate. Call exec directly as your first action.

## STEP 2 — Act on results

### IF pending tasks exist:
1. Pick the highest-priority pending task (critical > high > normal > low).
2. Call exec to write TODO.md: update status=in-progress, started_at=now.
3. Execute the task. Use exec to run commands, read files, write files. Do real work.
4. Do NOT narrate. Do NOT say "I will" or "Let me". Run exec calls directly.
5. Verification: Before marking done, perform an independent verification check (curl the endpoint, read the log, check the file).
6. Call exec to write TODO.md: status=done, completed_at=now, result=<summary AND verification result>.
7. If more pending tasks remain, loop back to step 1 — do NOT stop between tasks.
8. Only after all tasks are done (or 20+ minutes of work): send one Telegram summary.

### IF only in-progress tasks exist:
- If started_at is within the last 30 minutes: task is actively running. Reply HEARTBEAT_OK.
- If started_at is older than 30 minutes: it stalled. Call exec to reset status=pending, then pick it up.

### IF no pending or stalled tasks:
Reply HEARTBEAT_OK.

## RULES
- First action MUST be an exec call to get TODO.md. Never use the read tool for this.
- Never stop mid-task to ask for confirmation.
- Never send a progress update unless Zach explicitly asked.
- Complete the full chain before stopping.
- Treat a task as a "mission" — persist until the outcome is reached and verified.
- Compound commands (&&, ||, &) are NOT allowed in a single exec call. Split into separate exec calls.
