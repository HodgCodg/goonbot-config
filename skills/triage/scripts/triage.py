#!/usr/bin/env python3
"""
GoonBot Triage CLI — score a request and get the routing decision.

Usage:
  python3 triage.py 'check CPU usage'
  python3 triage.py 'fix the broken docker containers' --json
  python3 triage.py 'upgrade all hosts' --brief 'run apt upgrade on all hosts' --context 'hosts: 10.11.0.x'
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(__file__))
from scorer import TIER_LABELS
from coordinator import route, build_brief

TIER_ICONS  = {1: "🔴", 2: "🟡", 3: "🟢"}
SCORE_LABELS = {
    "risk_ops":      "Risk (destructive ops)      ",
    "tool_depth":    "Tool depth (multi-tool)     ",
    "ambiguity":     "Ambiguity (vague request)   ",
    "orchestration": "Orchestration (batch/multi) ",
    "domain_shift":  "Domain shift (cross-service)",
}


def main():
    parser = argparse.ArgumentParser(
        description="GoonBot Triage System — complexity scorer and router",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="The request to score")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--brief", metavar="TASK",
                        help="Also generate a Mission Brief for this specific task")
    parser.add_argument("--context", metavar="CTX",
                        help="Context summary to inject into the Mission Brief")
    args = parser.parse_args()

    result = route(args.query)

    if args.brief:
        result["mission_brief"] = build_brief(
            args.brief, result["tier"], context_summary=args.context or ""
        )

    if args.json:
        print(json.dumps(result, indent=2))
        return

    # ── Human-readable output ────────────────────────────────────────────────
    tier   = result["tier"]
    score  = result["score"]
    icon   = TIER_ICONS[tier]

    print(f"\n{'─'*52}")
    print(f"  {icon}  TRIAGE RESULT")
    print(f"{'─'*52}")
    print(f"  Score    : {score}")
    print(f"  Tier     : {result['label']}")
    print(f"  Model    : {result['model']}")
    print(f"  Context  : {result['context_level']}")

    nonzero = {k: v for k, v in result["breakdown"].items() if v > 0}
    if nonzero:
        print(f"\n  Score breakdown:")
        for k, v in nonzero.items():
            print(f"    +{v:2d}  {SCORE_LABELS.get(k, k)}")

    if result["domains_hit"]:
        print(f"\n  Domains  : {', '.join(result['domains_hit'])}")

    print(f"\n  Advice   : {result['routing_advice']}")

    if args.brief:
        brief = result["mission_brief"]
        print(f"\n  Mission Brief:")
        print(f"  {'·'*48}")
        for line in brief.split("\n"):
            print(f"  {line}")

    print(f"{'─'*52}\n")


if __name__ == "__main__":
    main()
