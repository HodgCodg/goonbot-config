# Autonomy Engine Protocols

## 1. The Reasoning Pulse
- **Frequency:** Every 60 minutes.
- **Mechanism:** Scheduled via `openclaw cron`.
- **Objective:** Perform a "System State Audit."
- **Audit Workflow:**
    1. Read `TODO.md`.
    2. For each `in-progress` task:
        - Check "Last Action" timestamp.
        - If > 60m without progress, flag as STALLED.
        - If STALLED, execute a diagnostic turn to identify the blocker.
    3. Evaluate environment (Disk usage, HA status, etc.).
    4. If a Critical task is active, send a "Pulse Report" to Zach.

## 2. State Tracking (TODO.md v2)
All tasks must follow the extended format:
`TASK-XXX | Status: [pending|in-progress|done|stalled] | Last Action: [YYYY-MM-DD HH:MM] | Expected Next: [Event/Time] | Blockers: [None|Detail]`

## 3. Proactive Escalation
- **Critical Priority:** Mandatory report every 30m.
- **Stall Recovery:** Automatic pivot to alternative strategy if the same command fails 3 times.
- **Silence Policy:** No "waiting for user" for Critical tasks; hypothesize, attempt, and report result.
