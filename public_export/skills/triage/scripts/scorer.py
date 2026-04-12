#!/usr/bin/env python3
"""
Complexity Scorer for GoonBot Triage System.
Analyzes a request and returns a complexity score + tier assignment.

Tiers:
  Tier 1 (score >= 8): Architect  -- handle directly, full context
  Tier 2 (score  4-7): Worker     -- subagent, moderate context
  Tier 3 (score  0-3): Utility    -- subagent, minimal context
"""
import re
import sys
from typing import Dict, List

TIER_1_MIN = 8
TIER_2_MIN = 4

TIER_MODELS = {
    1: "openrouter/google/gemma-4-31b-it:free",
    2: "openrouter/google/gemma-4-26b-a4b-it:free",
    3: "lmstudio/goonbot-current",
}

TIER_LABELS = {
    1: "Tier 1 — Architect (31B, direct, full context)",
    2: "Tier 2 — Worker (subagent, moderate context)",
    3: "Tier 3 — Utility (subagent, minimal context)",
}


class ComplexityScorer:
    WEIGHTS = {
        "risk_ops":      5,   # Destructive/irreversible operations
        "tool_depth":    2,   # Per extra distinct tool category (2+ = bonus)
        "ambiguity":     3,   # Vague/open-ended phrasing
        "orchestration": 4,   # Multi-system or batch scope
        "domain_shift":  3,   # Per extra domain beyond first (cross-service)
    }

    RISK_PATTERNS = [
        r"\brm\s+-[rf]", r"\bdd\b", r"\bmkfs\b",
        r"\bapt(-get)?\s+(install|upgrade|remove|purge)\b",
        r"\bpip\s+install\b", r"\bnpm\s+(install|update|upgrade)\b",
        r"\bchmod\b", r"\bchown\b",
        r"\bsystemctl\s+(stop|disable|mask|kill)\b",
        r"\bdocker\s+(rm|rmi|prune|stop)\b",
        r"\breboot\b", r"\bshutdown\b", r"\bpoweroff\b",
        r"\bformat\b", r"\bwipe\b",
        r"\bdrop\s+(table|database)\b", r"\btruncate\b",
        r"\bcurl.+\|\s*(bash|sh)\b", r"\bpasswd\b",
        r"\biptables\b", r"\bufw\s+(deny|delete)\b", r"\bcertbot\b",
        r"\boverwrite\b", r"\bdestroy\b",
    ]

    AMBIGUITY_PATTERNS = [
        r"\bfix\b", r"\bresolve\b", r"\bclean\s*up\b", r"\boptimize\b",
        r"\bimprove\b", r"\binvestigate\b", r"\blook\s+into\b",
        r"\bsort\s+out\b", r"\bdeal\s+with\b",
        r"\bfigure\s+out\b", r"\bcheck\s+on\b",
        r"\bwhat.*wrong\b", r"\bwhy.*not\s+work",
        r"\bseems.*broken\b", r"\bsomething.*off\b",
        r"\brefactor\b", r"\bdebug\b", r"\bdiagnose\b",
        r"\baudit\b", r"\breview\b",
    ]

    ORCHESTRATION_PATTERNS = [
        r"\ball\s+(hosts?|services?|containers?|nodes?|machines?|vms?)",
        r"\bevery\s+(host|service|node|machine)",
        r"\bbatch\b", r"\bsync(hronize)?\b",
        r"\bacross\s+(the|all|every)",
        r"\broll\s*out\b", r"\bdeploy\s+to\b",
        r"\bpropagat", r"\bfor\s+each\b", r"\bloop\s+(through|over)\b",
        r"\bcluster\b", r"\bfleet\b", r"\bmesh\b",
        r"\bmultiple\s+(hosts?|servers?|machines?)",
        r"\bparallel\b",
    ]

    DOMAINS = {
        "home_assistant": [r"\bhome\s*assistant\b", r"\bhass\b", r"\b(ha|home\s*assistant)\b", r"\bautomations?\b", r"\bentit(y|ies)\b"],
        "pfsense":        [r"\bpfsense\b", r"\bfirewall\b"],
        "proxmox":        [r"\bproxmox\b", r"\bpve\b", r"\bhypervisor\b", r"\b(vm|lxc)\s*\d"],
        "network":        [r"\bunifi\b", r"\bvlan\b", r"\bsubnet\b", r"\bdns\b", r"\bdhcp\b", r"\bswitch\b"],
        "docker":         [r"\bdocker\b", r"\bcontainer\b", r"\bcompose\b"],
        "botvm":          [r"\bbotvm\b", r"\bopenclaw\b", r"\bgoonbot\b"],
        "external":       [r"\btailscale\b", r"\bcloudflare\b", r"\bwireguard\b"],
    }

    def calculate(self, query: str) -> Dict:
        q = query.lower()
        breakdown = {}

        # Risk
        risk_hit = any(re.search(p, q) for p in self.RISK_PATTERNS)
        breakdown["risk_ops"] = self.WEIGHTS["risk_ops"] if risk_hit else 0

        # Tool depth: count distinct tool categories referenced
        tool_categories = {
            "read":   [r"\bread\b", r"\bcat\b", r"\bshow\b", r"\blist\b", r"\bget\b", r"\bstatus\b", r"\bview\b"],
            "write":  [r"\bwrite\b", r"\bedit\b", r"\bupdate\b", r"\bmodify\b", r"\bchange\b", r"\bcreate\b", r"\badd\b"],
            "exec":   [r"\brun\b", r"\bexec\b", r"\bstart\b", r"\brestart\b", r"\bstop\b", r"\blaunch\b"],
            "search": [r"\bsearch\b", r"\bfind\b", r"\blook\s+up\b", r"\bfetch\b", r"\bquery\b"],
            "ssh":    [r"\bssh\b", r"\bremote\b", r"\bon\s+(the\s+)?(host|server|machine)\b"],
            "net":    [r"\bping\b", r"\btraceroute\b", r"\bnslookup\b", r"\bdig\b", r"\bcurl\b", r"\bwget\b"],
        }
        tool_hits = sum(
            1 for patterns in tool_categories.values()
            if any(re.search(p, q) for p in patterns)
        )
        breakdown["tool_depth"] = max(0, tool_hits - 1) * self.WEIGHTS["tool_depth"]

        # Ambiguity
        ambig_hit = any(re.search(p, q) for p in self.AMBIGUITY_PATTERNS)
        breakdown["ambiguity"] = self.WEIGHTS["ambiguity"] if ambig_hit else 0

        # Orchestration
        orch_hit = any(re.search(p, q) for p in self.ORCHESTRATION_PATTERNS)
        breakdown["orchestration"] = self.WEIGHTS["orchestration"] if orch_hit else 0

        # Domain shift
        hit_domains = [
            name for name, patterns in self.DOMAINS.items()
            if any(re.search(p, q) for p in patterns)
        ]
        breakdown["domain_shift"] = max(0, len(hit_domains) - 1) * self.WEIGHTS["domain_shift"]

        total = sum(breakdown.values())
        tier = 1 if total >= TIER_1_MIN else (2 if total >= TIER_2_MIN else 3)

        return {
            "score": total,
            "tier": tier,
            "label": TIER_LABELS[tier],
            "model": TIER_MODELS[tier],
            "breakdown": breakdown,
            "domains_hit": hit_domains,
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: scorer.py '<query>'")
        sys.exit(1)
    r = ComplexityScorer().calculate(sys.argv[1])
    print(f"Score: {r['score']} | {r['label']}")
    nonzero = {k: v for k, v in r['breakdown'].items() if v > 0}
    if nonzero:
        print("Breakdown:", " + ".join(f"{k}:{v}" for k, v in nonzero.items()))
    if r["domains_hit"]:
        print("Domains:", ", ".join(r["domains_hit"]))
