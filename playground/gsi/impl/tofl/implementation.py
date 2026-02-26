from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import time

from remote.gsi.common.implementation import ImplementationBase

# from remote.gsi.impl.tofl.goal import GoalImpl
# from remote.gsi.impl.tofl.context import ContextImpl
# from remote.gsi.impl.tofl.dataModel import DataModelImpl
# from remote.gsi.impl.tofl.gsiProblem import GsiProblemImpl
# from remote.gsi.impl.tofl.strategy import StrategyImpl

class ImplementationImpl(ImplementationBase):
    def __init__(self):
        super().__init__()
        print("Time Of Flight Localization Problem: Implementation")