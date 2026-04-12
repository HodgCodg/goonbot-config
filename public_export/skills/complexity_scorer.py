#!/usr/bin/env python3
import re
import sys

class ComplexityScorer:
    # Scoring weights
    WEIGHTS = {
        'risk_ops': 5,      # rm, apt, write to core config
        'tool_depth': 2,    # requires multiple tools to complete
        'ambiguity': 3,     # vague phrasing ("fix it", "check things")
        'orchestration': 4, # mentions "all", "every", "multiple", "sync"
        'domain_shift': 3,  # spans HA, PfSense, and BotVM
    }

    def __init__(self, query):
        self.query = query.lower()

    def score(self):
        total = 0
        
        # Risk check
        risk_patterns = [r'rm\s+-rf', r'apt-get\s+install', r'apt\s+upgrade', r'chmod', r'chown']
        if any(re.search(p, self.query) for p in risk_patterns):
            total += self.WEIGHTS['risk_ops']

        # Tool depth check
        tool_patterns = [r'read', r'write', r'edit', r'exec', r'search', r'fetch']
        tool_count = sum(1 for p in tool_patterns if re.search(p, self.query))
        total += (tool_count * self.WEIGHTS['tool_depth'])

        # Ambiguity check
        ambiguous_patterns = [r'fix', r'update', r'check', r'look into', r'resolve']
        if any(re.search(p, self.query) for p in ambiguous_patterns):
            total += self.WEIGHTS['ambiguity']

        # Orchestration check
        orch_patterns = [r'all', r'every', r'multiple', r'synchronize', r'across', r'batch']
        if any(re.search(p, self.query) for p in orch_patterns):
            total += self.WEIGHTS['orchestration']

        # Domain shift check
        domains = ['home assistant', 'ha', 'pfsense', 'botvm', 'proxmox', 'orange pi']
        domain_count = sum(1 for d in domains if d in self.query)
        if domain_count > 1:
            total += self.WEIGHTS['domain_shift']

        return total

    def get_tier(self):
        s = self.score()
        if s >= 8: return 'Tier 1 (31B)'
        if s >= 4: return 'Tier 2 (26B)'
        return 'Tier 3 (Local)'

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: complexity_scorer.py '<query>'")
        sys.exit(1)
    
    q = sys.argv[1]
    scorer = ComplexityScorer(q)
    print(f"Score: {scorer.score()} | Tier: {scorer.get_tier()}")
