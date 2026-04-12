# Tiered Execution Flow (Triage)

This document defines the mandatory pre-execution phase for all GoonBot tasks.

## The Triage Loop

Before any task is started, the agent must execute the Triage Tool to determine the complexity and routing tier.

### 1. Triage Call
Run the following command:
`python3 /home/botvm/.openclaw/workspace/skills/triage/scripts/triage.py '<query>' --json`

### 2. Tier Mapping
| Tier | Score | Action | Model/Context |
|------|-------|--------|---------------|
| 🔴 T1 | 8+    | Architect | Handle directly. Full context. |
| 🟡 T2 | 4-7   | Worker | Spawn subagent. Moderate context. |
| 🟢 T3 | 0-3   | Utility | Spawn subagent. Minimal context. |

### 3. The Mission Brief
For T2 and T3 tasks, the agent must generate a **Mission Brief** before spawning the subagent.
The brief must include:
- **Objective:** Clear, single-sentence goal.
- **Constraints:** What NOT to do.
- **Tooling:** Which specific skills/scripts to use.
- **Verification:** How to prove the task is done.

### 4. Execution & Escalation
- If a T3/T2 subagent fails twice, the task is automatically escalated to T1.
- T1 (Architect) always performs the final verification check.

## Example Workflow
User: "Update all Pi nodes."
$\to$ Triage: Score 9 (Orchestration + Risk) $\to$ Tier 1.
$\to$ Architect handles directly.

User: "Check the weather in Beloit."
$\to$ Triage: Score 1 (Simple) $\to$ Tier 3.
$\to$ Spawn Utility subagent $\to$ Mission Brief $\to$ Result.
