# Research Report: Tiered Subagent Scaling Architecture
**Project:** GoonBot Dynamic Scaling
**Target Implementer:** Claude / Lead Architect
**Status:** Draft Proposal

## 1. Architectural Overview
The goal is to optimize resource usage (VRAM/Compute) while maintaining high output quality. We transition from a "flat" agent structure to a "pyramidal" structure where task complexity determines the intelligence tier assigned.

### The Tier Hierarchy
| Tier | Model | Role | Max Concurrency | Primary Strength |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Gemma 4 31B | Architect / Router | 3-4 | Strategic planning, complex logic, final audit |
| **Tier 2** | Gemma 4 26B | Specialist / Worker | 3-4 | Iterative coding, detailed research, data processing |
| **Tier 3** | Local/Current | Utility / Executor | 2 | Simple shell commands, status checks, file reads |

---

## 2. The Orchestration Loop

### Step A: The Complexity Router (Tier 1)
Every new request enters Tier 1. The Router does not execute the task but analyzes it:
- **Low Complexity**: (e.g., "Check CPU", "Read file X") $\rightarrow$ Route to Tier 3.
- **Medium Complexity**: (e.g., "Refactor this function", "Search and summarize X") $\rightarrow$ Route to Tier 2.
- **High Complexity**: (e.g., "Design a new system", "Debug cross-service crash") $\rightarrow$ Keep in Tier 1.

### Step B: Execution & Quality Gates
When a task is delegated to Tier 2 or 3, it is wrapped in a **Quality Gate**.
1. **Execution**: Subagent produces a result.
2. **Verification**:
   - **Tier 3 $\rightarrow$ Tier 2**: A Tier 2 agent audits the result for correctness.
   - **Tier 2 $\rightarrow$ Tier 1**: A Tier 1 agent audits the result against the original goal.
3. **Score**: Results are graded (Pass / Fail / Marginal).

### Step C: Dynamic Escalation (The "Upward Push")
If a result fails the Quality Gate:
- **Failure at Tier 3**: Task is escalated to Tier 2 with the previous failed attempt attached as "Lesson Learned."
- **Failure at Tier 2**: Task is escalated to Tier 1 for manual override or strategic correction.
- **Repeat Failure**: If Tier 1 fails twice, the system triggers a "User Intervention Required" alert.

---

## 3. Implementation Logic for Claude

### Routing Prompt (The "Triage" Prompt)
The Router should use a prompt similar to:
*"Analyze the following task. Assign it a complexity score (1-10). 1-3: Tier 3, 4-7: Tier 2, 8-10: Tier 1. Output ONLY the tier number and a brief justification."*

### State Machine
Implement using a state-based graph (e.g., LangGraph pattern):
`Entry` $\rightarrow$ `Route` $\rightarrow$ `Execute(Tier X)` $\rightarrow$ `Evaluate` $\rightarrow$ `(Success? Done : Escalate)`.

---

## 4. Expected Benefits
1. **VRAM Optimization**: Prevents the 31B model from being bogged down by trivial "read file" tasks.
2. **Increased Throughput**: Tier 3 agents can run faster/lighter, freeing up Tier 1 for high-value cognitive work.
3. **Self-Healing**: The escalation loop ensures that errors are caught by a more capable model before reaching the user.
