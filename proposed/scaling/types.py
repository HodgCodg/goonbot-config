from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

class Tier(Enum):
    TIER_1_ARCHITECT = auto()  # 31B: Complex planning, orchestration, final verification
    TIER_2_WORKER = auto()     # 26B: Standard task execution, iterative tool use
    TIER_3_UTILITY = auto()    # Local: Fast checks, simple shell commands, local reads

@dataclass
class ComplexityScore:
    total_score: int
    breakdown: Dict[str, int]
    assigned_tier: Tier

@dataclass
class AgentTask:
    task_id: str
    query: str
    original_context: str
    pruned_context: Optional[str] = None
    current_tier: Optional[Tier] = None
    attempts: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class TaskResult:
    success: bool
    output: str
    verified_by: Optional[Tier] = None
    error: Optional[str] = None
