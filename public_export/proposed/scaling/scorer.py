from .types import Tier, ComplexityScore, AgentTask, TaskResult
import re

class ComplexityScorer:
    """
    Blueprint for query complexity analysis.
    Logic used to determine which tier of agent is required for a given task.
    """
    
    WEIGHTS = {
        'risk_ops': 5,      # Destructive operations (rm, apt upgrade)
        'tool_depth': 2,    # Required number of distinct tool calls
        'ambiguity': 3,     # Vague phrasing ("Fix the dashboard")
        'orchestration': 4, # Multi-system operations ("All hosts", "Synchronize")
        'domain_shift': 3,  # Spans multiple services (HA + PfSense + BotVM)
    }

    def calculate_score(self, query: str) -> ComplexityScore:
        # Logic skeleton: 
        # 1. Run regex patterns for risk, tools, and keywords.
        # 2. Sum weights.
        # 3. Map score to Tier.
        # Implementation left for Claude Opus.
        pass

    def map_to_tier(self, score: int) -> Tier:
        if score >= 8: return Tier.TIER_1_ARCHITECT
        if score >= 4: return Tier.TIER_2_WORKER
        return Tier.TIER_3_UTILITY
