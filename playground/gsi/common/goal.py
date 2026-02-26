from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import time

from remote.gsi.common.context import ContextBase, StateType, ActionType, ResultType
# from remote.gsi.common.implementation import ImplementationBase
# from remote.gsi.common.strategy import StrategyBase

class GoalBase(ABC, Generic[StateType, ResultType]):
    """
    Goal: A function on which to optimize.
    
    Defines the objective function and constraints for a problem.
    A goal is satisfied when evaluate() returns a value meeting the success criteria.
    """
    
    def __init__(self, name: str, context: Optional[ContextBase] = None):
        print("Goal Base CTOR")
        self.name = name
        self.context = context or ContextBase()
        self.status = GSIStatus.NOT_STARTED
    
    @abstractmethod
    def evaluate(self, state: StateType) -> float:
        """
        Evaluate how well the current state satisfies the goal.
        
        Returns:
            float: Objective value (lower is better by convention)
                   Return 0.0 for perfect satisfaction
                   Return float('inf') for constraint violations
        """
        pass
    
    @abstractmethod
    def is_satisfied(self, state: StateType) -> bool:
        """
        Check if the goal is sufficiently satisfied.
        
        Returns:
            bool: True if goal constraints are met
        """
        pass
    
    def check_feasibility(self) -> bool:
        """
        Check if the goal is feasible given the context constraints.
        
        Returns:
            bool: True if goal can potentially be satisfied
        """
        return True  # Default: assume feasible unless proven otherwise