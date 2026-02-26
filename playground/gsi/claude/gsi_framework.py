"""
GSI Framework: Goal-Strategy-Implementation Architecture

Mathematical Foundation:
- Goal: A function to optimize (objective + constraints)
- Strategy: A solution to the optimization problem
- Implementation: The executable realization of the strategy
- Context: Environmental state and problem parameters
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import time

# Type variables for generic GSI problems
StateType = TypeVar('StateType')
ActionType = TypeVar('ActionType')
ResultType = TypeVar('ResultType')


class GSIStatus(Enum):
    """Execution status of a GSI problem"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    INFEASIBLE = "infeasible"


@dataclass
class Context:
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


class Goal(ABC, Generic[StateType, ResultType]):
    """
    Goal: A function on which to optimize.
    
    Defines the objective function and constraints for a problem.
    A goal is satisfied when evaluate() returns a value meeting the success criteria.
    """
    
    def __init__(self, name: str, context: Optional[Context] = None):
        self.name = name
        self.context = context or Context()
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


class Strategy(ABC, Generic[StateType, ActionType, ResultType]):
    """
    Strategy: A solution to the optimization problem.
    
    Defines the algorithmic approach to achieving the goal.
    Maps from current state to actions that move toward goal satisfaction.
    """
    
    def __init__(self, name: str, goal: Goal[StateType, ResultType]):
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


class Implementation(ABC, Generic[StateType, ActionType, ResultType]):
    """
    Implementation: The collection of details on which the strategy is implemented.
    
    The executable realization that actually performs actions in the world.
    Handles low-level details: hardware interfaces, timing, error handling.
    """
    
    def __init__(self, name: str, strategy: Strategy[StateType, ActionType, ResultType]):
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


class GSIProblem(Generic[StateType, ActionType, ResultType]):
    """
    Complete GSI Problem: Ties together Goal, Strategy, and Implementation.
    
    Provides the main execution loop for autonomous behavior.
    """
    
    def __init__(
        self,
        goal: Goal[StateType, ResultType],
        strategy: Strategy[StateType, ActionType, ResultType],
        implementation: Implementation[StateType, ActionType, ResultType],
        max_iterations: int = 100,
    ):
        self.goal = goal
        self.strategy = strategy
        self.implementation = implementation
        self.max_iterations = max_iterations
        
        self.iteration = 0
        self.history = []
    
    def solve(self) -> GSIStatus:
        """
        Main execution loop: run until goal satisfied or max iterations.
        
        Returns:
            GSIStatus: Final execution status
        """
        # Check feasibility
        if not self.goal.check_feasibility():
            self.goal.status = GSIStatus.INFEASIBLE
            return GSIStatus.INFEASIBLE
        
        self.goal.status = GSIStatus.RUNNING
        
        for self.iteration in range(self.max_iterations):
            # Observe current state
            state = self.implementation.observe()
            
            # Check if goal satisfied
            if self.goal.is_satisfied(state):
                self.goal.status = GSIStatus.SUCCESS
                return GSIStatus.SUCCESS
            
            # Plan next action
            action = self.strategy.plan(state)
            
            # Verify action safety
            if not self.strategy.verify(state, action):
                self.goal.status = GSIStatus.FAILED
                return GSIStatus.FAILED
            
            # Execute action
            t0 = time.perf_counter()
            result = self.implementation.execute(action)
            execution_time = time.perf_counter() - t0
            
            self.implementation.execution_count += 1
            self.implementation.last_execution_time = execution_time
            
            # Record history
            self.history.append({
                'iteration': self.iteration,
                'state': state,
                'action': action,
                'result': result,
                'objective': self.goal.evaluate(state),
                'execution_time': execution_time,
            })
            
            # Allow strategy to adapt
            self.strategy.adapt(result)
        
        # Max iterations reached without satisfaction
        self.goal.status = GSIStatus.FAILED
        return GSIStatus.FAILED
    
    def get_report(self) -> Dict[str, Any]:
        """Generate execution report with statistics."""
        if not self.history:
            return {'status': 'not_executed'}
        
        execution_times = [h['execution_time'] for h in self.history]
        objectives = [h['objective'] for h in self.history]
        
        return {
            'status': self.goal.status.value,
            'iterations': len(self.history),
            'final_objective': objectives[-1] if objectives else None,
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'max_execution_time': max(execution_times),
            'objective_improvement': objectives[0] - objectives[-1] if len(objectives) > 1 else 0,
        }
