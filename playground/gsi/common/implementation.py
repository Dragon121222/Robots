from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import time

from remote.gsi.common.context import ContextBase, StateType, ActionType, ResultType

# from remote.gsi.common.goal import GoalBase
from remote.gsi.common.strategy import StrategyBase

class ImplementationBase(ABC, Generic[StateType, ActionType, ResultType]):
    """
    implementation: The collection of details on which the strategy is implemented.
    
    The executable realization that actually performs actions in the world.
    Handles low-level details: hardware interfaces, timing, error handling.
    """
    
    def __init__(self, name: str, strategy: Strategy[StateType, ActionType, ResultType]):
        print("Implementation Base CTOR")
        self.name = name
        self.strategy = strategy
        self.execution_count = 0
        self.last_execution_time = 0.0


    @abstractmethod
    def execute(self, action: ActionType) -> ResultType:
        """
        Execute an action in the real world.
        
        Args:
            action: Action to perform
            
        Returns:
            ResultType: Result of execution
        """
        pass
    
    @abstractmethod
    def observe(self) -> StateType:
        """
        Observe the current state of the world.
        
        Returns:
            StateType: Current state observation
        """
        pass
    
    def measure_performance(self) -> Dict[str, float]:
        """
        Measure implementation performance metrics.
        
        Returns:
            Dict of performance metrics (latency, success rate, etc.)
        """
        return {
            'execution_count': self.execution_count,
            'last_execution_time': self.last_execution_time,
        }