from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import time

from remote.gsi.common.context import ContextBase, StateType, ActionType, ResultType

from remote.gsi.common.goal import GoalBase
from remote.gsi.common.implementation import ImplementationBase
from remote.gsi.common.strategy import StrategyBase

class GsiProblemBase(Generic[StateType, ActionType, ResultType]):
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
        print("GsiProblem Base CTOR")
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
