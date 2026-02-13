
class SimpleState:
    def __init__(self,stateId,otherParams=None):
        self._stateId = stateId
        self._otherParams = otherParams


class SimpleFsm:
    def __init__(
        self,
        stateMap: dict[str, set[str]],
        initialState: SimpleState,
        onEnter=None,
        onExit=None,
        onFailedTransition=None,
        onDeadStates=None
    ):
        self._initialState          = initialState
        self._currentState          = initialState
        self._stateMap              = stateMap
        self._onEnter               = onEnter or self.trivialOnEnter
        self._onExit                = onExit or self.trivialOnExit
        self._onFailedTransition    = onFailedTransition or self.trivialOnFailedTransition
        self._onDeadStates          = onDeadStates or self.trivialOnDeadStates

        self._deadStates            = self.checkUnreachableStates(
                                        self._stateMap,
                                        self._initialState._stateId
                                    )

        self._onDeadStates(self._deadStates)

    def requestUpdate(self,newState: SimpleState,requestor):
        if newState._stateId in self._stateMap[self._currentState._stateId]:
            self._onExit(self._currentState,requestor)
            self._onEnter(newState,requestor)
            self._currentState = newState
        else:
            self._onFailedTransition(newState,requestor)

    def trivialOnEnter(self,newState: SimpleState,requestor):
        print(f"Going to new state: {newState._stateId} as requested by {requestor}")

    def trivialOnExit(self,currentState: SimpleState,requestor):
        print(f"Exiting current state: {currentState._stateId} as requested by {requestor}")

    def trivialOnFailedTransition(self,newState: SimpleState,requestor):
        print(f"Can't transition to new state: {newState._stateId} as requested by {requestor}")

    def checkUnreachableStates(self, state_map: dict[str, set[str]], initial: str) -> set[str]:
        all_states = set(state_map.keys())
        for targets in state_map.values():
            all_states |= targets
        visited, queue = set(), [initial]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            queue.extend(state_map.get(current, set()) - visited)
        return all_states - visited

    def trivialOnDeadStates(self, deadStatesSet: set[str]):
        if len(deadStatesSet) > 0:
            print("Warning: Dead States Exist!")
            print(f"{deadStatesSet}")