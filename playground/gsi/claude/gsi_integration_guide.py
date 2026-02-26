"""
Integration Guide: Using GSI Framework with Existing Robot Code

This shows how to refactor your current main.py to use the GSI framework
while preserving your existing IPC architecture.
"""

# ============================================================================
# Option 1: Minimal Integration - Just wrap existing behavior
# ============================================================================

def option1_minimal_wrapper():
    """
    Wrap your existing centering logic in GSI without changing architecture.
    
    This lets you:
    - Track execution metrics
    - Get structured reports
    - Compose behaviors hierarchically
    
    Without disrupting your working IPC system.
    """
    
    # Your existing imports
    from remote.common.fakeIpc import FakeIpc as ipcManager
    from remote.camera.simpleCamera import simpleCam as cameraManager
    from remote.vision.simpleOrangePiNpuYolo import simpleOrangePiNpuYolo as yoloManager
    from remote.buzzer.droid_sounds import DroidSpeaker as buzzerManager
    from remote.servo.servoCommander import ServoCommander as servoManager
    
    # GSI imports
    from gsi_centering_example import create_centering_problem
    
    # Initialize hardware (as you do now)
    buzzer = buzzerManager()
    camera = cameraManager(width=1920, height=1080)
    yolo = yoloManager()
    servo = servoManager()
    
    # Create IPC (as you do now)
    ipc = ipcManager({
        "buzzer": buzzer,
        "camera": camera,
        "yolo": yolo,
        "servo": servo
    })
    
    # NEW: Create GSI problem
    centering = create_centering_problem(
        target_class="person",
        camera=camera,
        yolo=yolo,
        servo=servo,
        ipc=ipc,
        tolerance=50.0,
        max_iterations=20,
    )
    
    # Initialize
    ipc.send("Online", "buzzer")
    ipc.send("setup", "servo")
    
    # Execute centering behavior using GSI
    status = centering.solve()
    
    # Get structured report
    report = centering.get_report()
    print(f"Centering result: {report}")
    
    if status.value == "success":
        ipc.send("FOUND", "buzzer")
    else:
        ipc.send("LOST", "buzzer")


# ============================================================================
# Option 2: Hybrid - Keep IPC, Add GSI Control Layer  
# ============================================================================

def option2_hybrid_control():
    """
    Use your existing components as Implementations,
    but add GSI layer for behavior composition and metrics.
    
    Benefits:
    - Compose multiple behaviors
    - Switch between goals dynamically
    - Track performance over time
    - Build toward hierarchical planning
    """
    
    from remote.common.fakeIpc import FakeIpc as ipcManager
    from remote.camera.simpleCamera import simpleCam as cameraManager
    from remote.vision.simpleOrangePiNpuYolo import simpleOrangePiNpuYolo as yoloManager
    from remote.buzzer.droid_sounds import DroidSpeaker as buzzerManager
    from remote.servo.servoCommander import ServoCommander as servoManager
    
    from gsi_centering_example import create_centering_problem
    import time
    
    # Initialize hardware
    buzzer = buzzerManager()
    camera = cameraManager(width=1920, height=1080)
    yolo = yoloManager()
    servo = servoManager()
    
    ipc = ipcManager({
        "buzzer": buzzer,
        "camera": camera,
        "yolo": yolo,
        "servo": servo
    })
    
    ipc.send("Online", "buzzer")
    ipc.send("setup", "servo")
    
    # Create a behavior library
    behaviors = {
        "center_person": create_centering_problem(
            target_class="person",
            camera=camera, yolo=yolo, servo=servo, ipc=ipc,
            tolerance=50.0,
        ),
        "center_cat": create_centering_problem(
            target_class="cat",
            camera=camera, yolo=yolo, servo=servo, ipc=ipc,
            tolerance=60.0,
        ),
        "center_dog": create_centering_problem(
            target_class="dog",
            camera=camera, yolo=yolo, servo=servo, ipc=ipc,
            tolerance=60.0,
        ),
    }
    
    # Simple behavior selection loop
    current_behavior = "center_person"
    
    try:
        while True:
            print(f"\nExecuting: {current_behavior}")
            
            # Execute current behavior
            status = behaviors[current_behavior].solve()
            report = behaviors[current_behavior].get_report()
            
            print(f"Result: {report}")
            
            # Behavior switching logic (placeholder)
            # In future: this becomes your "strategic layer"
            if status.value == "success":
                ipc.send("SUCCESS", "buzzer")
                time.sleep(2)
            else:
                ipc.send("SEARCHING", "buzzer")
                # Could switch to different target
                time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")


# ============================================================================
# Option 3: Full GSI - Refactor Everything
# ============================================================================

def option3_full_gsi():
    """
    Full refactor: Everything is a GSI problem.
    
    Benefits:
    - Unified architecture
    - Easy to add new behaviors
    - Clear dependency tracking
    - Built-in metrics and debugging
    
    Drawbacks:
    - More upfront work
    - Requires rethinking some patterns
    """
    
    from gsi_framework import GSIProblem, Goal, Strategy, Implementation, Context
    from gsi_problem_catalog import get_problem, get_by_tier, ProblemTier
    import numpy as np
    
    # Print what we're building toward
    print("GSI Problem Catalog:")
    print("="*70)
    
    primitives = get_by_tier(ProblemTier.PRIMITIVE)
    print(f"\nPrimitives to implement: {len(primitives)}")
    for p in primitives[:3]:  # Show first 3
        print(f"  - {p.name}")
    
    behaviors = get_by_tier(ProblemTier.BEHAVIOR)
    print(f"\nBehaviors to implement: {len(behaviors)}")
    for p in behaviors[:3]:
        print(f"  - {p.name}")
    
    strategic = get_by_tier(ProblemTier.STRATEGIC)
    print(f"\nStrategic capabilities to implement: {len(strategic)}")
    for p in strategic:
        print(f"  - {p.name}")
    
    print("\n" + "="*70)
    print("Recommended path: Start with Option 1 or 2, migrate to 3 over time")


# ============================================================================
# RECOMMENDED: Start with Option 2
# ============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║              GSI Framework Integration Guide                      ║
╚══════════════════════════════════════════════════════════════════╝

Three integration options:

OPTION 1: Minimal Wrapper
  ✓ Keep all existing code
  ✓ Just wrap main behavior in GSI
  ✓ Get metrics and reports
  ✓ 30 minutes work
  
OPTION 2: Hybrid Control (RECOMMENDED)
  ✓ Keep existing IPC architecture
  ✓ Add GSI control layer
  ✓ Easy to compose behaviors
  ✓ Path toward strategic planning
  ✓ 2-3 hours work
  
OPTION 3: Full Refactor
  ✓ Everything is GSI
  ✓ Cleanest architecture
  ✓ Most future-proof
  ✓ 1-2 weeks work

Recommendation: Start with Option 2, migrate to Option 3 as you add
new behaviors from the problem catalog.

Next steps:
1. Run: python gsi_problem_catalog.py
   (See all defined problems)
   
2. Pick one primitive to implement:
   - forward_kinematics (enables IK)
   - object_tracking (enables follow behavior)
   
3. Use the GSI framework template:
   - Define Goal (what to optimize)
   - Define Strategy (how to optimize)
   - Define Implementation (hardware interface)
   - Wire together into GSIProblem
   
4. Execute and get metrics automatically
    """)
    
    print("\n" + "="*70)
    print("Running Option 3 demo (catalog preview):")
    print("="*70)
    option3_full_gsi()
