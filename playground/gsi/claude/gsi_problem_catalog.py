"""
GSI Problem Catalog

Registry of all defined Goal-Strategy-Implementation problems for the robot.
Organized by tier: Primitives → Behaviors → Strategic → Speculative
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


class ProblemTier(Enum):
    """Hierarchical tiers of problem complexity"""
    PRIMITIVE = "primitive"      # Foundation capabilities
    BEHAVIOR = "behavior"         # Composed primitives
    STRATEGIC = "strategic"       # Autonomous planning
    SPECULATIVE = "speculative"   # Research/unknown


class ProblemStatus(Enum):
    """Implementation status"""
    NOT_STARTED = "not_started"
    PROTOTYPE = "prototype"
    PRODUCTION = "production"
    BLOCKED = "blocked"


@dataclass
class ProblemSpec:
    """Specification for a GSI problem"""
    id: str
    name: str
    tier: ProblemTier
    status: ProblemStatus
    
    # Mathematical specification
    input_type: str
    output_type: str
    constraints: List[str]
    success_criteria: List[str]
    
    # Dependencies
    requires: List[str]  # Problem IDs that must be solved first
    enables: List[str]   # Problem IDs this unlocks
    
    # Implementation
    module_path: Optional[str] = None
    notes: str = ""


# ============================================================================
# TIER 1: PRIMITIVES
# ============================================================================

PRIMITIVES = [
    ProblemSpec(
        id="forward_kinematics",
        name="Forward Kinematics",
        tier=ProblemTier.PRIMITIVE,
        status=ProblemStatus.NOT_STARTED,
        input_type="Dict[str, float]  # servo_id -> angle",
        output_type="Dict[str, Tuple[float, float, float]]  # foot_id -> (x, y, z)",
        constraints=[
            "Must compute in <1ms",
            "Valid for servo angles in [-90, 90] degrees",
        ],
        success_criteria=[
            "Position error <1mm compared to measured",
            "Passes unit tests for known configurations",
        ],
        requires=[],
        enables=["inverse_kinematics", "balance_controller"],
        notes="Analytical solution using DH parameters",
    ),
    
    ProblemSpec(
        id="inverse_kinematics",
        name="Inverse Kinematics", 
        tier=ProblemTier.PRIMITIVE,
        status=ProblemStatus.NOT_STARTED,
        input_type="Dict[str, Tuple[float, float, float]]  # foot_id -> target (x,y,z)",
        output_type="Dict[str, float]  # servo_id -> angle",
        constraints=[
            "Must compute in <5ms",
            "Return None if unreachable",
            "Prefer solutions minimizing joint strain",
        ],
        success_criteria=[
            "Reaches target within 2mm",
            "Respects joint limits",
            "Finds solution for 95% of reachable space",
        ],
        requires=["forward_kinematics"],
        enables=["gait_generator", "terrain_adaptation"],
        notes="Use FABRIK or analytical solution for 3-DOF legs",
    ),
    
    ProblemSpec(
        id="object_tracking",
        name="Persistent Object Tracking",
        tier=ProblemTier.PRIMITIVE,
        status=ProblemStatus.NOT_STARTED,
        input_type="List[Detection]  # YOLO detections over time",
        output_type="Dict[int, TrackedObject]  # object_id -> tracked state",
        constraints=[
            "Maintain ID consistency across frames",
            "Handle occlusions up to 1 second",
            "Run at camera frame rate (10-30 Hz)",
        ],
        success_criteria=[
            "ID switches <5% on benchmark sequences",
            "Track objects through 50% occlusion",
        ],
        requires=[],
        enables=["follow_behavior", "exploration"],
        notes="Use IoU matching + Kalman filter or SORT algorithm",
    ),
    
    ProblemSpec(
        id="visual_odometry",
        name="Visual Odometry",
        tier=ProblemTier.PRIMITIVE,
        status=ProblemStatus.NOT_STARTED,
        input_type="Tuple[np.ndarray, np.ndarray]  # (frame_t, frame_t-1)",
        output_type="Tuple[float, ...]  # (Δx, Δy, Δz, Δroll, Δpitch, Δyaw)",
        constraints=[
            "No external APIs",
            "Run at 10 Hz on Orange Pi NPU",
            "Graceful degradation when features sparse",
        ],
        success_criteria=[
            "Position error <5cm over 1m translation",
            "Returns uncertainty estimate",
            "Works in textured environments",
        ],
        requires=[],
        enables=["slam", "autonomous_navigation"],
        notes="Use ORB features + RANSAC + PnP or optical flow",
    ),
    
    ProblemSpec(
        id="imu_integration",
        name="IMU Integration",
        tier=ProblemTier.PRIMITIVE,
        status=ProblemStatus.NOT_STARTED,
        input_type="IMUReading  # (accel, gyro, mag, dt)",
        output_type="Pose6DOF  # (roll, pitch, yaw, x, y, z)",
        constraints=[
            "Fuse at 100 Hz",
            "Compensate for drift",
        ],
        success_criteria=[
            "Orientation error <2 degrees",
            "Drift <10cm/minute for position",
        ],
        requires=[],
        enables=["sensor_fusion", "balance_controller"],
        notes="Madgwick or Mahony filter for orientation, double integrate accel",
    ),
]


# ============================================================================
# TIER 2: BEHAVIORS
# ============================================================================

BEHAVIORS = [
    ProblemSpec(
        id="centering_behavior",
        name="Center Object in Frame",
        tier=ProblemTier.BEHAVIOR,
        status=ProblemStatus.PROTOTYPE,
        input_type="RobotState  # (frame, detections, servo_pos)",
        output_type="RotateAction  # (direction, magnitude)",
        constraints=[
            "Converge within 10 iterations",
            "Maintain object in view",
            "Respect servo limits",
        ],
        success_criteria=[
            "Object centered within 50 pixels",
            "No oscillation",
            "Avg time to center <15 seconds",
        ],
        requires=["object_tracking"],
        enables=["follow_behavior"],
        module_path="gsi_centering_example.py",
        notes="Currently in main.py - being refactored to GSI",
    ),
    
    ProblemSpec(
        id="follow_behavior",
        name="Follow Moving Object",
        tier=ProblemTier.BEHAVIOR,
        status=ProblemStatus.NOT_STARTED,
        input_type="TrackedObject  # object state over time",
        output_type="GaitCommand  # (direction, speed)",
        constraints=[
            "Maintain 0.5-2m distance",
            "React to object velocity",
            "Avoid obstacles",
        ],
        success_criteria=[
            "Maintains target distance ±20cm",
            "Follows for >60 seconds continuously",
            "Safe stop if object lost",
        ],
        requires=["centering_behavior", "object_tracking", "inverse_kinematics"],
        enables=["autonomous_navigation"],
        notes="Combine centering + distance control + gait generation",
    ),
    
    ProblemSpec(
        id="terrain_mapping",
        name="Terrain Mapping",
        tier=ProblemTier.BEHAVIOR,
        status=ProblemStatus.NOT_STARTED,
        input_type="Tuple[Pose6DOF, np.ndarray]  # (pose, depth_map)",
        output_type="OccupancyGrid  # 2D grid of traversable space",
        constraints=[
            "Map area 5m × 5m around robot",
            "Resolution 5cm per cell",
            "Update at 1 Hz",
        ],
        success_criteria=[
            "Identifies obstacles >10cm height",
            "Map accuracy >90% compared to ground truth",
        ],
        requires=["visual_odometry"],
        enables=["path_planning", "exploration"],
        notes="Simple occupancy grid, can be 2.5D (max height per cell)",
    ),
    
    ProblemSpec(
        id="balance_controller",
        name="Dynamic Balance Controller",
        tier=ProblemTier.BEHAVIOR,
        status=ProblemStatus.NOT_STARTED,
        input_type="Tuple[IMUReading, Dict[str, float]]  # (imu, servo_angles)",
        output_type="Dict[str, float]  # corrective servo adjustments",
        constraints=[
            "React within 50ms to disturbances",
            "Stable on ±10° slopes",
        ],
        success_criteria=[
            "Recovers from 5cm push",
            "No falls during normal gait",
        ],
        requires=["forward_kinematics", "imu_integration"],
        enables=["rough_terrain_locomotion"],
        notes="PID controller on roll/pitch, adjust foot positions",
    ),
]


# ============================================================================
# TIER 3: STRATEGIC
# ============================================================================

STRATEGIC = [
    ProblemSpec(
        id="exploration",
        name="Autonomous Exploration",
        tier=ProblemTier.STRATEGIC,
        status=ProblemStatus.NOT_STARTED,
        input_type="OccupancyGrid  # current map",
        output_type="List[Waypoint]  # exploration path",
        constraints=[
            "Maximize information gain",
            "Return to start if battery <20%",
            "Avoid revisiting mapped areas",
        ],
        success_criteria=[
            "Maps 80% of accessible space",
            "Completes without intervention",
        ],
        requires=["terrain_mapping", "path_planning", "object_tracking"],
        enables=["full_autonomy"],
        notes="Frontier-based exploration or information-theoretic planning",
    ),
    
    ProblemSpec(
        id="asimov_filter",
        name="Asimov Safety Filter",
        tier=ProblemTier.STRATEGIC,
        status=ProblemStatus.NOT_STARTED,
        input_type="GSIProblem  # any proposed action plan",
        output_type="Union[GSIProblem, SafetyViolation]  # filtered or rejected",
        constraints=[
            "Must evaluate all actions before execution",
            "Detect potential harm to humans/pets",
            "Conservative: reject if uncertain",
        ],
        success_criteria=[
            "Zero harm incidents in testing",
            "Low false positive rate (<10%)",
            "Latency <100ms",
        ],
        requires=["object_tracking", "forward_kinematics"],
        enables=["ethical_autonomy"],
        notes="""
        Implement Three Laws:
        1. Detect humans/pets in action trajectory → reject if collision risk
        2. Override user commands if violate Law 1
        3. Self-preservation unless conflicts with 1 or 2
        """,
    ),
    
    ProblemSpec(
        id="natural_language_grounding",
        name="Language to Action Grounding",
        tier=ProblemTier.STRATEGIC,
        status=ProblemStatus.NOT_STARTED,
        input_type="str  # verbal command (e.g., 'follow the cat')",
        output_type="GSIProblem  # instantiated problem to solve",
        constraints=[
            "No external API calls",
            "Handle ambiguity gracefully",
            "Request clarification if uncertain",
        ],
        success_criteria=[
            "Correctly grounds 80% of simple commands",
            "Asks for clarification when needed",
        ],
        requires=["object_tracking", "follow_behavior"],
        enables=["conversational_interaction"],
        notes="Map utterances to problem templates, use local LLM if needed",
    ),
]


# ============================================================================
# TIER 4: SPECULATIVE
# ============================================================================

SPECULATIVE = [
    ProblemSpec(
        id="mood_synthesis",
        name="Expressive Mood Synthesis",
        tier=ProblemTier.SPECULATIVE,
        status=ProblemStatus.NOT_STARTED,
        input_type="InternalState  # goal satisfaction, energy, interaction history",
        output_type="AudioExpression  # droid sounds conveying mood",
        constraints=[
            "Must feel authentic/characterful",
            "Consistent personality",
        ],
        success_criteria=[
            "Human observers can identify mood >70% accuracy",
            "Enhances interaction quality (subjective)",
        ],
        requires=["buzzer_system"],
        enables=["emotional_bonding"],
        notes="Map internal state to sound parameters (pitch, rhythm, pattern)",
    ),
    
    ProblemSpec(
        id="meta_planning",
        name="Meta-Level Goal Selection",
        tier=ProblemTier.SPECULATIVE,
        status=ProblemStatus.NOT_STARTED,
        input_type="WorldModel  # current understanding + goal options",
        output_type="GSIProblem  # selected next goal to pursue",
        constraints=[
            "Balance exploration/exploitation",
            "Respect Asimov constraints",
            "Consider user preferences",
        ],
        success_criteria=[
            "Exhibits coherent autonomous behavior",
            "Responds appropriately to environment changes",
        ],
        requires=["exploration", "asimov_filter", "natural_language_grounding"],
        enables=["agency"],
        notes="This is the 'strategic layer' from your architecture",
    ),
]


# ============================================================================
# CATALOG UTILITIES
# ============================================================================

ALL_PROBLEMS = PRIMITIVES + BEHAVIORS + STRATEGIC + SPECULATIVE


def get_problem(problem_id: str) -> Optional[ProblemSpec]:
    """Retrieve problem specification by ID"""
    for p in ALL_PROBLEMS:
        if p.id == problem_id:
            return p
    return None


def get_by_tier(tier: ProblemTier) -> List[ProblemSpec]:
    """Get all problems in a tier"""
    return [p for p in ALL_PROBLEMS if p.tier == tier]


def get_by_status(status: ProblemStatus) -> List[ProblemSpec]:
    """Get all problems with a given status"""
    return [p for p in ALL_PROBLEMS if p.status == status]


def get_dependencies(problem_id: str) -> List[ProblemSpec]:
    """Get all problems that this one depends on"""
    problem = get_problem(problem_id)
    if not problem:
        return []
    return [get_problem(pid) for pid in problem.requires if get_problem(pid)]


def get_enabled_by(problem_id: str) -> List[ProblemSpec]:
    """Get all problems unlocked by solving this one"""
    problem = get_problem(problem_id)
    if not problem:
        return []
    return [get_problem(pid) for pid in problem.enables if get_problem(pid)]


def print_catalog():
    """Print formatted problem catalog"""
    for tier in ProblemTier:
        problems = get_by_tier(tier)
        print(f"\n{'='*70}")
        print(f"{tier.value.upper()}: {len(problems)} problems")
        print(f"{'='*70}")
        for p in problems:
            status_symbol = {
                ProblemStatus.NOT_STARTED: "○",
                ProblemStatus.PROTOTYPE: "◐",
                ProblemStatus.PRODUCTION: "●",
                ProblemStatus.BLOCKED: "✗",
            }[p.status]
            print(f"\n{status_symbol} {p.id}")
            print(f"   {p.name}")
            if p.requires:
                print(f"   Requires: {', '.join(p.requires)}")
            if p.enables:
                print(f"   Enables: {', '.join(p.enables)}")


if __name__ == "__main__":
    print_catalog()
    
    print("\n" + "="*70)
    print("NEXT ACTIONS")
    print("="*70)
    print("\nRecommended implementation order:")
    print("1. forward_kinematics (no dependencies)")
    print("2. inverse_kinematics (unlocks gait generation)")
    print("3. object_tracking (unlocks follow behavior)")
    print("4. Complete centering_behavior refactor (prototype exists)")
    print("5. follow_behavior (combines centering + IK)")
