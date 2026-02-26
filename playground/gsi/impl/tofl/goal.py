from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import time

from remote.gsi.impl.tofl.context import ContextImpl

from remote.gsi.common.goal import GoalBase

# from remote.gsi.impl.tofl.dataModel import DataModelImpl
# from remote.gsi.impl.tofl.gsiProblem import GsiProblemImpl
# from remote.gsi.impl.tofl.implementation import ImplementationImpl
# from remote.gsi.impl.tofl.strategy import StrategyImpl

class GoalImpl(GoalBase):
    def __init__(self):
        super().__init__(
            name="Time Of Flight Localization Problem",
            context=Context(
                constraints={
                    'computational': {
                        'max_latency_ms': 100
                    },
                    'physical': {
                        'x': 0, 
                        'y': 0,
                        'z': 0,
                        'r': 0,
                        'p': 0,
                        'y': 0
                    },
                    'safety': {
                        'require_detection': True
                    }
                }
            )
        )
        print("Time Of Flight Localization Problem: Goal")