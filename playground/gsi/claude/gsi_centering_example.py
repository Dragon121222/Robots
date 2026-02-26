"""
Concrete GSI Example: Object Centering Behavior

Goal: Center detected object in camera frame
Strategy: Proportional control based on bounding box position  
Implementation: Servo commands to rotate robot
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass
from gsi_framework import Goal, Strategy, Implementation, GSIProblem, Context


# ============================================================================
# State and Action Types
# ============================================================================

@dataclass
class RobotState:
    """Current state of the robot"""
    frame: np.ndarray  # Camera frame
    detections: list  # YOLO detections
    servo_positions: dict  # Current servo angles
    timestamp: float


@dataclass
class RotateAction:
    """Action: Rotate left or right"""
    direction: str  # "left" or "right"
    magnitude: float  # Degrees to rotate (0-20)


@dataclass
class CenteringResult:
    """Result of executing a centering action"""
    success: bool
    new_center_x: Optional[float]
    error: Optional[str]


# ============================================================================
# Goal: Center Object in Frame
# ============================================================================

class CenterObjectGoal(Goal[RobotState, CenteringResult]):
    """
    Goal: Center the detected object in the camera frame.
    
    Objective: Minimize horizontal distance between object center and frame center
    Constraint: Object must be detected in frame
    """
    
    def __init__(self, target_class: str, tolerance: float = 50.0):
        super().__init__(
            name=f"Center {target_class} in frame",
            context=Context(
                constraints={
                    'computational': {'max_latency_ms': 100},
                    'physical': {'min_bbox_area': 5000, 'max_rotation_deg': 20},
                    'safety': {'require_detection': True}
                }
            )
        )
        self.target_class = target_class
        self.tolerance = tolerance  # pixels
    
    def evaluate(self, state: RobotState) -> float:
        """
        Evaluate centering error.
        
        Returns:
            Pixel distance from center (0.0 = perfect)
            inf if no detection
        """
        detection = self._find_target(state)
        if detection is None:
            return float('inf')
        
        frame_w = state.frame.shape[1]
        frame_center = frame_w / 2
        
        bbox = detection['bbox']
        bbox_center_x = (bbox[0] + bbox[2]) / 2
        
        error = abs(bbox_center_x - frame_center)
        return error
    
    def is_satisfied(self, state: RobotState) -> bool:
        """Goal satisfied if object centered within tolerance."""
        error = self.evaluate(state)
        return error <= self.tolerance
    
    def check_feasibility(self) -> bool:
        """Feasible if we can physically rotate and detect objects."""
        # Could check: camera functional, servos responsive, etc.
        return True
    
    def _find_target(self, state: RobotState) -> Optional[dict]:
        """Find target object in detections."""
        for det in state.detections:
            if det['class_name'] == self.target_class:
                return det
        return None


# ============================================================================
# Strategy: Proportional Control
# ============================================================================

class ProportionalCenteringStrategy(Strategy[RobotState, RotateAction, CenteringResult]):
    """
    Strategy: Proportional control to center object.
    
    Action is proportional to centering error:
    - Large error → large rotation
    - Small error → small rotation
    """
    
    def __init__(self, goal: CenterObjectGoal, gain: float = 0.05):
        super().__init__(name="Proportional centering", goal=goal)
        self.gain = gain  # Proportional gain
        self.deadband = 50.0  # pixels - don't act if error < deadband
    
    def plan(self, state: RobotState) -> RotateAction:
        """
        Plan rotation based on proportional error.
        
        Error > 0 → object right of center → rotate right
        Error < 0 → object left of center → rotate left
        """
        # Find target
        detection = None
        for det in state.detections:
            if det['class_name'] == self.goal.target_class:
                detection = det
                break
        
        if detection is None:
            # No detection - don't move
            return RotateAction(direction="none", magnitude=0.0)
        
        # Calculate error
        frame_w = state.frame.shape[1]
        frame_center = frame_w / 2
        bbox = detection['bbox']
        bbox_center_x = (bbox[0] + bbox[2]) / 2
        
        error = bbox_center_x - frame_center
        
        # Within deadband - don't act
        if abs(error) < self.deadband:
            return RotateAction(direction="none", magnitude=0.0)
        
        # Proportional control
        magnitude = min(abs(error) * self.gain, 20.0)  # Cap at 20 degrees
        direction = "right" if error > 0 else "left"
        
        return RotateAction(direction=direction, magnitude=magnitude)
    
    def verify(self, state: RobotState, action: RotateAction) -> bool:
        """
        Verify action is safe.
        
        Safety checks:
        - Magnitude within physical limits
        - Object still detected (avoid blind rotation)
        """
        # Check magnitude
        max_rotation = self.goal.context.constraints['physical']['max_rotation_deg']
        if action.magnitude > max_rotation:
            return False
        
        # Check detection still present
        detection = None
        for det in state.detections:
            if det['class_name'] == self.goal.target_class:
                detection = det
                break
        
        if detection is None and action.magnitude > 0:
            # Don't rotate if we've lost the object
            return False
        
        return True
    
    def adapt(self, feedback: CenteringResult) -> None:
        """Adapt strategy based on results (optional)."""
        # Could implement: increase gain if converging slowly, etc.
        pass


# ============================================================================
# Implementation: Robot Hardware Interface
# ============================================================================

class RobotCenteringImplementation(Implementation[RobotState, RotateAction, CenteringResult]):
    """
    Implementation: Execute centering actions on actual robot hardware.
    
    Interfaces with:
    - Camera (via ipc.send to camera component)
    - YOLO (via ipc.send to yolo component)  
    - Servos (via ipc.send to servo component)
    """
    
    def __init__(
        self,
        strategy: Strategy,
        camera,
        yolo,
        servo,
        ipc,
    ):
        super().__init__(name="Robot centering", strategy=strategy)
        self.camera = camera
        self.yolo = yolo
        self.servo = servo
        self.ipc = ipc
        
        # State cache
        self.last_frame = None
        self.last_detections = []
    
    def execute(self, action: RotateAction) -> CenteringResult:
        """
        Execute rotation action.
        
        Sends command to servo system via IPC.
        """
        import time
        
        t0 = time.perf_counter()
        
        if action.direction == "none":
            # No action needed
            return CenteringResult(
                success=True,
                new_center_x=None,
                error=None
            )
        
        # Send rotation command
        if action.direction == "left":
            self.ipc.send("left", "servo")
        elif action.direction == "right":
            self.ipc.send("right", "servo")
        
        # Wait for servo motion to complete
        time.sleep(1.5)  # This should match your servo timing
        
        # Capture new frame to verify
        self.ipc.send("snap_yolo", "camera")
        time.sleep(0.1)  # Wait for processing
        
        self.last_execution_time = time.perf_counter() - t0
        self.execution_count += 1
        
        # Get new center position
        new_center = None
        if self.last_detections:
            for det in self.last_detections:
                if det['class_name'] == self.strategy.goal.target_class:
                    bbox = det['bbox']
                    new_center = (bbox[0] + bbox[2]) / 2
                    break
        
        return CenteringResult(
            success=True,
            new_center_x=new_center,
            error=None
        )
    
    def observe(self) -> RobotState:
        """
        Observe current robot state.
        
        Returns current frame, detections, servo positions.
        """
        import time
        
        # In your architecture, state is updated via callbacks
        # This is a simplified version - in practice you'd query
        # the actual current state from your IPC system
        
        return RobotState(
            frame=self.last_frame if self.last_frame is not None else np.zeros((480, 640, 3)),
            detections=self.last_detections,
            servo_positions={},  # Could query actual servo positions
            timestamp=time.perf_counter()
        )
    
    def update_state(self, frame: np.ndarray, detections: list):
        """
        Update state cache (called by your IPC callbacks).
        """
        self.last_frame = frame
        self.last_detections = detections


# ============================================================================
# Factory Function
# ============================================================================

def create_centering_problem(
    target_class: str,
    camera,
    yolo,
    servo,
    ipc,
    tolerance: float = 50.0,
    gain: float = 0.05,
    max_iterations: int = 20,
) -> GSIProblem:
    """
    Factory function to create a complete centering GSI problem.
    
    Args:
        target_class: Object class to center (e.g., "person", "cat")
        camera, yolo, servo, ipc: Hardware components
        tolerance: Centering tolerance in pixels
        gain: Proportional control gain
        max_iterations: Max iterations before giving up
    
    Returns:
        Configured GSIProblem ready to solve()
    """
    goal = CenterObjectGoal(target_class, tolerance)
    strategy = ProportionalCenteringStrategy(goal, gain)
    implementation = RobotCenteringImplementation(strategy, camera, yolo, servo, ipc)
    
    return GSIProblem(
        goal=goal,
        strategy=strategy,
        implementation=implementation,
        max_iterations=max_iterations,
    )


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    """
    Example: How to integrate with your existing main.py
    """
    
    # This is pseudocode showing integration pattern:
    
    # 1. Create your existing components
    # camera = cameraManager()
    # yolo = yoloManager()
    # servo = servoManager()
    # ipc = ipcManager(...)
    
    # 2. Create GSI problem
    # centering_problem = create_centering_problem(
    #     target_class="person",
    #     camera=camera,
    #     yolo=yolo,
    #     servo=servo,
    #     ipc=ipc,
    #     tolerance=50.0,
    #     gain=0.05,
    #     max_iterations=20,
    # )
    
    # 3. Execute
    # status = centering_problem.solve()
    
    # 4. Get report
    # report = centering_problem.get_report()
    # print(f"Centering completed: {report}")
    
    print("GSI Centering Problem - see integration example above")
