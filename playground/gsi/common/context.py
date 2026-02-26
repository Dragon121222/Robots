from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import time

# from remote.gsi.common.goal import GoalBase
# from remote.gsi.common.gsiProblem import GsiProblemBase
# from remote.gsi.common.implementation import ImplementationBase
# from remote.gsi.common.strategy import StrategyBase

# Type variables for generic GSI problems
StateType = TypeVar('StateType')
ActionType = TypeVar('ActionType')
ResultType = TypeVar('ResultType')

class GsiStatusBase(Enum):
    """Execution status of a GSI problem"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    INFEASIBLE = "infeasible"

@dataclass
class ContextBase:
    """
    Context: The collection of details around a {Goal, Strategy, Implementation} problem.
    
    Captures environmental state, constraints, and metadata needed for execution.
    """
    timestamp: float = field(default_factory=time.perf_counter)
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Ensure we have basic constraint categories
        if 'computational' not in self.constraints:
            self.constraints['computational'] = {}
        if 'physical' not in self.constraints:
            self.constraints['physical'] = {}
        if 'safety' not in self.constraints:
            self.constraints['safety'] = {}

    def __init__(self):
        print("Context Base CTOR")