from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import time

from remote.gsi.common.context import ContextBase, StateType, ActionType, ResultType

from remote.gsi.common.goal import GoalBase
# from remote.gsi.common.Implementation import ImplementationBase

class StrategyBase(ABC, Generic[StateType, ActionType, ResultType]):
    """
    Strategy: A solution to the optimization problem.
    
    Defines the algorithmic approach to achieving the goal.
    Maps from current state to actions that move toward goal satisfaction.
    """
    
    def __init__(self, name: str, goal: Goal[StateType, ResultType]):
        print("Strategy Base CTOR")
        self.name = name
        self.goal = goal
    
    @abstractmethod
    def plan(self, state: StateType) -> ActionType:
        """
        Generate the next action to take from the current state.
        
        Args:
            state: Current system state
            
        Returns:
            ActionType: Action to execute
        """
        pass
    
    @abstractmethod
    def verify(self, state: StateType, action: ActionType) -> bool:
        """
        Verify that a planned action is safe and valid.
        
        Args:
            state: Current system state
            action: Proposed action
            
        Returns:
            bool: True if action is safe to execute
        """
        pass
    
    def adapt(self, feedback: Any) -> None:
        """
        Adapt strategy based on execution feedback (optional).
        
        Args:
            feedback: Execution results or environmental changes
        """
        pass