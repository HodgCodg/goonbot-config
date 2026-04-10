#!/usr/bin/env python3
"""
Coordinator for GoonBot Triage System.
Generates routing decisions and context-pruned Mission Briefs for subagents.
"""
import sys
import json
import os
sys.path.insert(0, os.path.dirname(__file__))
from scorer import ComplexityScorer, TIER_MODELS, TIER_LABELS

CONTEXT_LEVELS = {
    1: "FULL — complete session history, all workspace context",
    2: "MODERATE — last 5 exchanges + directly relevant files only",
    3: "MINIMAL — task description only, no prior context needed",
}

ROUTING_ADVICE = {
    1: (
        "Handle directly. Apply architect-level reasoning: plan, execute, verify. "
        "No subagent needed — this task requires full context and strategic oversight."
    ),
    2: (
        "Spawn a subagent. Provide: task description + last 5 exchanges + relevant file paths. "
        "Verify the subagent result before reporting to user. Escalate to Tier 1 if it fails."
    ),
    3: (
        "Spawn a subagent. Provide: task description only (+ hostname/path if needed). "
        "For read-only ops, trust the result. For writes, do a quick verify. "
        "Escalate to Tier 2 if the subagent reports uncertainty or error."
    ),
}


def route(query: str) -> dict:
    """Score a query and return the full routing decision."""
    scorer = ComplexityScorer()
    result = scorer.calculate(query)
    result["context_level"] = CONTEXT_LEVELS[result["tier"]]
    result["routing_advice"] = ROUTING_ADVICE[result["tier"]]
    return result


def build_brief(task: str, tier: int, context_summary: str = "") -> str:
    """
    Generate a context-pruned Mission Brief for a subagent.

    Args:
        task:            The concrete task to execute.
        tier:            The tier (1/2/3) determining context depth.
        context_summary: Optional — a summary of relevant session context.
    """
    ctx_block = f"\n\nCONTEXT:\n{context_summary}" if context_summary else ""

    if tier == 3:
        return (
            f"TASK: {task}{ctx_block}\n\n"
            "Execute this task directly and concisely. "
            "Report the result only — no preamble."
        )
    elif tier == 2:
        return (
            f"TASK: {task}{ctx_block}\n\n"
            "Execute step-by-step. Verify success before reporting. "
            "Report: what you did, the result, and any warnings or anomalies."
        )
    else:
        return (
            f"TASK: {task}{ctx_block}\n\n"
            "Apply full architectural reasoning. "
            "Follow: Plan → Execute → Verify → Report. "
            "Do not skip verification."
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: coordinator.py '<query>'")
        sys.exit(1)
    result = route(sys.argv[1])
    print(json.dumps(result, indent=2))
