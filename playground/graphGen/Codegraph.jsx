import { useEffect, useRef, useState, useCallback } from "react";
import * as d3 from "d3";

const SAMPLE_DATA = {"nodes": [{"id": "robot_py_3e0ed9", "type": "module", "name": "robot", "qualified_name": "robot", "language": "python", "loc": {"file": "robot.py", "line_start": 1, "line_end": 0, "col_start": 0}, "metadata": {}}, {"id": "__future___annotations_6a7860", "type": "import", "name": "annotations", "qualified_name": "__future__.annotations", "language": "python", "loc": {"file": "robot.py", "line_start": 2, "line_end": 2, "col_start": 0}, "metadata": {"module": "__future__", "symbol": "annotations"}}, {"id": "asyncio_7778fb", "type": "import", "name": "asyncio", "qualified_name": "asyncio", "language": "python", "loc": {"file": "robot.py", "line_start": 3, "line_end": 3, "col_start": 0}, "metadata": {"module": "asyncio"}}, {"id": "numpy_27a793", "type": "import", "name": "np", "qualified_name": "numpy", "language": "python", "loc": {"file": "robot.py", "line_start": 4, "line_end": 4, "col_start": 0}, "metadata": {"module": "numpy"}}, {"id": "typing_Optional_c424ac", "type": "import", "name": "Optional", "qualified_name": "typing.Optional", "language": "python", "loc": {"file": "robot.py", "line_start": 5, "line_end": 5, "col_start": 0}, "metadata": {"module": "typing", "symbol": "Optional"}}, {"id": "typing_List_1f40eb", "type": "import", "name": "List", "qualified_name": "typing.List", "language": "python", "loc": {"file": "robot.py", "line_start": 5, "line_end": 5, "col_start": 0}, "metadata": {"module": "typing", "symbol": "List"}}, {"id": "dataclasses_dataclass_8a23ef", "type": "import", "name": "dataclass", "qualified_name": "dataclasses.dataclass", "language": "python", "loc": {"file": "robot.py", "line_start": 6, "line_end": 6, "col_start": 0}, "metadata": {"module": "dataclasses", "symbol": "dataclass"}}, {"id": "pathlib_Path_cbfd99", "type": "import", "name": "Path", "qualified_name": "pathlib.Path", "language": "python", "loc": {"file": "robot.py", "line_start": 7, "line_end": 7, "col_start": 0}, "metadata": {"module": "pathlib", "symbol": "Path"}}, {"id": "robot_Pose_fc358c", "type": "class", "name": "Pose", "qualified_name": "robot.Pose", "language": "python", "loc": {"file": "robot.py", "line_start": 11, "line_end": 14, "col_start": 0}, "metadata": {"bases": [], "decorators": ["dataclass"]}}, {"id": "robot_Pose_x_774446", "type": "variable", "name": "x", "qualified_name": "robot.Pose.x", "language": "python", "loc": {"file": "robot.py", "line_start": 12, "line_end": 12, "col_start": 4}, "metadata": {"type_annotation": "float"}}, {"id": "robot_Pose_y_62fdf0", "type": "variable", "name": "y", "qualified_name": "robot.Pose.y", "language": "python", "loc": {"file": "robot.py", "line_start": 13, "line_end": 13, "col_start": 4}, "metadata": {"type_annotation": "float"}}, {"id": "robot_Pose_theta_a33f1c", "type": "variable", "name": "theta", "qualified_name": "robot.Pose.theta", "language": "python", "loc": {"file": "robot.py", "line_start": 14, "line_end": 14, "col_start": 4}, "metadata": {"type_annotation": "float"}}, {"id": "robot_Sensor_792041", "type": "class", "name": "Sensor", "qualified_name": "robot.Sensor", "language": "python", "loc": {"file": "robot.py", "line_start": 17, "line_end": 28, "col_start": 0}, "metadata": {"bases": [], "decorators": []}}, {"id": "robot_Sensor___init___9f9d40", "type": "method", "name": "__init__", "qualified_name": "robot.Sensor.__init__", "language": "python", "loc": {"file": "robot.py", "line_start": 19, "line_end": 22, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "name", "type": "str"}, {"name": "rate_hz", "type": "float"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_Sensor_read_bf0c29", "type": "method", "name": "read", "qualified_name": "robot.Sensor.read", "language": "python", "loc": {"file": "robot.py", "line_start": 24, "line_end": 25, "col_start": 4}, "metadata": {"params": [{"name": "self"}], "return_type": "Optional[np.ndarray]", "async": false, "decorators": []}}, {"id": "robot_Sensor_calibrate_cccaac", "type": "method", "name": "calibrate", "qualified_name": "robot.Sensor.calibrate", "language": "python", "loc": {"file": "robot.py", "line_start": 27, "line_end": 28, "col_start": 4}, "metadata": {"params": [{"name": "self"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_Kinect_90b3cc", "type": "class", "name": "Kinect", "qualified_name": "robot.Kinect", "language": "python", "loc": {"file": "robot.py", "line_start": 31, "line_end": 51, "col_start": 0}, "metadata": {"bases": ["Sensor"], "decorators": []}}, {"id": "robot_Kinect_DEPTH_WIDTH_340c4e", "type": "variable", "name": "DEPTH_WIDTH", "qualified_name": "robot.Kinect.DEPTH_WIDTH", "language": "python", "loc": {"file": "robot.py", "line_start": 33, "line_end": 33, "col_start": 4}, "metadata": {"type_annotation": null}}, {"id": "robot_Kinect_DEPTH_HEIGHT_25057a", "type": "variable", "name": "DEPTH_HEIGHT", "qualified_name": "robot.Kinect.DEPTH_HEIGHT", "language": "python", "loc": {"file": "robot.py", "line_start": 34, "line_end": 34, "col_start": 4}, "metadata": {"type_annotation": null}}, {"id": "robot_Kinect___init___97f1aa", "type": "method", "name": "__init__", "qualified_name": "robot.Kinect.__init__", "language": "python", "loc": {"file": "robot.py", "line_start": 36, "line_end": 40, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "device_id", "type": "int"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_Kinect_read_949966", "type": "method", "name": "read", "qualified_name": "robot.Kinect.read", "language": "python", "loc": {"file": "robot.py", "line_start": 42, "line_end": 43, "col_start": 4}, "metadata": {"params": [{"name": "self"}], "return_type": "Optional[np.ndarray]", "async": false, "decorators": []}}, {"id": "robot_Kinect_read_rgb_dd0ae1", "type": "method", "name": "read_rgb", "qualified_name": "robot.Kinect.read_rgb", "language": "python", "loc": {"file": "robot.py", "line_start": 45, "line_end": 46, "col_start": 4}, "metadata": {"params": [{"name": "self"}], "return_type": "Optional[np.ndarray]", "async": false, "decorators": []}}, {"id": "robot_Kinect_get_pointcloud_ced8a3", "type": "method", "name": "get_pointcloud", "qualified_name": "robot.Kinect.get_pointcloud", "language": "python", "loc": {"file": "robot.py", "line_start": 48, "line_end": 51, "col_start": 4}, "metadata": {"params": [{"name": "self"}], "return_type": "np.ndarray", "async": false, "decorators": []}}, {"id": "robot_WheelLegActuator_c15691", "type": "class", "name": "WheelLegActuator", "qualified_name": "robot.WheelLegActuator", "language": "python", "loc": {"file": "robot.py", "line_start": 54, "line_end": 71, "col_start": 0}, "metadata": {"bases": [], "decorators": []}}, {"id": "robot_WheelLegActuator_MAX_TORQUE_NM_b7c10d", "type": "variable", "name": "MAX_TORQUE_NM", "qualified_name": "robot.WheelLegActuator.MAX_TORQUE_NM", "language": "python", "loc": {"file": "robot.py", "line_start": 56, "line_end": 56, "col_start": 4}, "metadata": {"type_annotation": null}}, {"id": "robot_WheelLegActuator___init___79ce68", "type": "method", "name": "__init__", "qualified_name": "robot.WheelLegActuator.__init__", "language": "python", "loc": {"file": "robot.py", "line_start": 58, "line_end": 61, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "joint_id", "type": "int"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_WheelLegActuator_set_torque_cf05b7", "type": "method", "name": "set_torque", "qualified_name": "robot.WheelLegActuator.set_torque", "language": "python", "loc": {"file": "robot.py", "line_start": 63, "line_end": 65, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "torque_nm", "type": "float"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_WheelLegActuator__apply_torque_2515e3", "type": "method", "name": "_apply_torque", "qualified_name": "robot.WheelLegActuator._apply_torque", "language": "python", "loc": {"file": "robot.py", "line_start": 67, "line_end": 68, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "torque", "type": "float"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_WheelLegActuator_step_5943e5", "type": "method", "name": "step", "qualified_name": "robot.WheelLegActuator.step", "language": "python", "loc": {"file": "robot.py", "line_start": 70, "line_end": 71, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "dt", "type": "float"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_LocomotionController_9d6ac0", "type": "class", "name": "LocomotionController", "qualified_name": "robot.LocomotionController", "language": "python", "loc": {"file": "robot.py", "line_start": 74, "line_end": 100, "col_start": 0}, "metadata": {"bases": [], "decorators": []}}, {"id": "robot_LocomotionController___init___2d0ff7", "type": "method", "name": "__init__", "qualified_name": "robot.LocomotionController.__init__", "language": "python", "loc": {"file": "robot.py", "line_start": 76, "line_end": 79, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "num_legs", "type": "int"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_LocomotionController_walk_946007", "type": "method", "name": "walk", "qualified_name": "robot.LocomotionController.walk", "language": "python", "loc": {"file": "robot.py", "line_start": 81, "line_end": 84, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "vx", "type": "float"}, {"name": "vy", "type": "float"}, {"name": "omega", "type": "float"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_LocomotionController__compute_torq_fec2ad", "type": "method", "name": "_compute_torques", "qualified_name": "robot.LocomotionController._compute_torques", "language": "python", "loc": {"file": "robot.py", "line_start": 86, "line_end": 87, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "vx", "type": "float"}, {"name": "vy", "type": "float"}, {"name": "omega", "type": "float"}], "return_type": "List[float]", "async": false, "decorators": []}}, {"id": "robot_LocomotionController_update_cbe0b1", "type": "method", "name": "update", "qualified_name": "robot.LocomotionController.update", "language": "python", "loc": {"file": "robot.py", "line_start": 89, "line_end": 93, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "dt", "type": "float"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_LocomotionController__update_pose_9ca0c5", "type": "method", "name": "_update_pose", "qualified_name": "robot.LocomotionController._update_pose", "language": "python", "loc": {"file": "robot.py", "line_start": 95, "line_end": 100, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "dt", "type": "float"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_YOLODetector_9d4023", "type": "class", "name": "YOLODetector", "qualified_name": "robot.YOLODetector", "language": "python", "loc": {"file": "robot.py", "line_start": 103, "line_end": 128, "col_start": 0}, "metadata": {"bases": [], "decorators": []}}, {"id": "robot_YOLODetector___init___ba1eb7", "type": "method", "name": "__init__", "qualified_name": "robot.YOLODetector.__init__", "language": "python", "loc": {"file": "robot.py", "line_start": 105, "line_end": 108, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "model_path", "type": "Path"}, {"name": "input_size", "type": "tuple"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_YOLODetector_load_b82b48", "type": "method", "name": "load", "qualified_name": "robot.YOLODetector.load", "language": "python", "loc": {"file": "robot.py", "line_start": 110, "line_end": 111, "col_start": 4}, "metadata": {"params": [{"name": "self"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_YOLODetector_detect_f44872", "type": "method", "name": "detect", "qualified_name": "robot.YOLODetector.detect", "language": "python", "loc": {"file": "robot.py", "line_start": 113, "line_end": 117, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "frame", "type": "np.ndarray"}], "return_type": "List[dict]", "async": false, "decorators": []}}, {"id": "robot_YOLODetector__run_inference_9eba26", "type": "method", "name": "_run_inference", "qualified_name": "robot.YOLODetector._run_inference", "language": "python", "loc": {"file": "robot.py", "line_start": 119, "line_end": 120, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "frame", "type": "np.ndarray"}], "return_type": "np.ndarray", "async": false, "decorators": []}}, {"id": "robot_YOLODetector__postprocess_c26522", "type": "method", "name": "_postprocess", "qualified_name": "robot.YOLODetector._postprocess", "language": "python", "loc": {"file": "robot.py", "line_start": 122, "line_end": 128, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "raw", "type": "np.ndarray"}], "return_type": "List[dict]", "async": false, "decorators": []}}, {"id": "robot_RobotBrain_893384", "type": "class", "name": "RobotBrain", "qualified_name": "robot.RobotBrain", "language": "python", "loc": {"file": "robot.py", "line_start": 131, "line_end": 161, "col_start": 0}, "metadata": {"bases": [], "decorators": []}}, {"id": "robot_RobotBrain___init___5f1b6b", "type": "method", "name": "__init__", "qualified_name": "robot.RobotBrain.__init__", "language": "python", "loc": {"file": "robot.py", "line_start": 133, "line_end": 138, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "config_path", "type": "Path"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_RobotBrain_run_20beec", "type": "method", "name": "run", "qualified_name": "robot.RobotBrain.run", "language": "python", "loc": {"file": "robot.py", "line_start": 140, "line_end": 146, "col_start": 4}, "metadata": {"params": [{"name": "self"}], "return_type": null, "async": true, "decorators": []}}, {"id": "robot_RobotBrain__tick_f2f344", "type": "method", "name": "_tick", "qualified_name": "robot.RobotBrain._tick", "language": "python", "loc": {"file": "robot.py", "line_start": 148, "line_end": 153, "col_start": 4}, "metadata": {"params": [{"name": "self"}], "return_type": null, "async": true, "decorators": []}}, {"id": "robot_RobotBrain__react_c315da", "type": "method", "name": "_react", "qualified_name": "robot.RobotBrain._react", "language": "python", "loc": {"file": "robot.py", "line_start": 155, "line_end": 158, "col_start": 4}, "metadata": {"params": [{"name": "self"}, {"name": "detections", "type": "List[dict]"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_RobotBrain_stop_51f993", "type": "method", "name": "stop", "qualified_name": "robot.RobotBrain.stop", "language": "python", "loc": {"file": "robot.py", "line_start": 160, "line_end": 161, "col_start": 4}, "metadata": {"params": [{"name": "self"}], "return_type": null, "async": false, "decorators": []}}, {"id": "robot_main_4009b8", "type": "function", "name": "main", "qualified_name": "robot.main", "language": "python", "loc": {"file": "robot.py", "line_start": 164, "line_end": 166, "col_start": 0}, "metadata": {"params": [], "return_type": null, "async": false, "decorators": []}}], "edges": [{"id": "e_robot_py___future_imports", "source": "robot_py_3e0ed9", "target": "__future___annotations_6a7860", "type": "imports", "metadata": {}}, {"id": "e_robot_py_asyncio__imports", "source": "robot_py_3e0ed9", "target": "asyncio_7778fb", "type": "imports", "metadata": {}}, {"id": "e_robot_py_numpy_27_imports", "source": "robot_py_3e0ed9", "target": "numpy_27a793", "type": "imports", "metadata": {}}, {"id": "e_robot_py_typing_O_imports", "source": "robot_py_3e0ed9", "target": "typing_Optional_c424ac", "type": "imports", "metadata": {}}, {"id": "e_robot_py_typing_L_imports", "source": "robot_py_3e0ed9", "target": "typing_List_1f40eb", "type": "imports", "metadata": {}}, {"id": "e_robot_py_dataclas_imports", "source": "robot_py_3e0ed9", "target": "dataclasses_dataclass_8a23ef", "type": "imports", "metadata": {}}, {"id": "e_robot_py_pathlib__imports", "source": "robot_py_3e0ed9", "target": "pathlib_Path_cbfd99", "type": "imports", "metadata": {}}, {"id": "e_robot_py_robot_Po_contains", "source": "robot_py_3e0ed9", "target": "robot_Pose_fc358c", "type": "contains", "metadata": {}}, {"id": "e_robot_Po_robot_Po_contains", "source": "robot_Pose_fc358c", "target": "robot_Pose_x_774446", "type": "contains", "metadata": {}}, {"id": "e_robot_Po_robot_Po_contains", "source": "robot_Pose_fc358c", "target": "robot_Pose_y_62fdf0", "type": "contains", "metadata": {}}, {"id": "e_robot_Po_robot_Po_contains", "source": "robot_Pose_fc358c", "target": "robot_Pose_theta_a33f1c", "type": "contains", "metadata": {}}, {"id": "e_robot_py_robot_Se_contains", "source": "robot_py_3e0ed9", "target": "robot_Sensor_792041", "type": "contains", "metadata": {}}, {"id": "e_robot_Se_robot_Se_contains", "source": "robot_Sensor_792041", "target": "robot_Sensor___init___9f9d40", "type": "contains", "metadata": {}}, {"id": "e_robot_Se_robot_Se_contains", "source": "robot_Sensor_792041", "target": "robot_Sensor_read_bf0c29", "type": "contains", "metadata": {}}, {"id": "e_robot_Se_robot_Se_contains", "source": "robot_Sensor_792041", "target": "robot_Sensor_calibrate_cccaac", "type": "contains", "metadata": {}}, {"id": "e_robot_py_robot_Ki_contains", "source": "robot_py_3e0ed9", "target": "robot_Kinect_90b3cc", "type": "contains", "metadata": {}}, {"id": "e_robot_Ki_robot_Ki_contains", "source": "robot_Kinect_90b3cc", "target": "robot_Kinect_DEPTH_WIDTH_340c4e", "type": "contains", "metadata": {}}, {"id": "e_robot_Ki_robot_Ki_contains", "source": "robot_Kinect_90b3cc", "target": "robot_Kinect_DEPTH_HEIGHT_25057a", "type": "contains", "metadata": {}}, {"id": "e_robot_Ki_robot_Ki_contains", "source": "robot_Kinect_90b3cc", "target": "robot_Kinect___init___97f1aa", "type": "contains", "metadata": {}}, {"id": "e_robot_Ki_robot_Ki_contains", "source": "robot_Kinect_90b3cc", "target": "robot_Kinect_read_949966", "type": "contains", "metadata": {}}, {"id": "e_robot_Ki_robot_Ki_contains", "source": "robot_Kinect_90b3cc", "target": "robot_Kinect_read_rgb_dd0ae1", "type": "contains", "metadata": {}}, {"id": "e_robot_Ki_robot_Ki_contains", "source": "robot_Kinect_90b3cc", "target": "robot_Kinect_get_pointcloud_ced8a3", "type": "contains", "metadata": {}}, {"id": "e_robot_py_robot_Wh_contains", "source": "robot_py_3e0ed9", "target": "robot_WheelLegActuator_c15691", "type": "contains", "metadata": {}}, {"id": "e_robot_Wh_robot_Wh_contains", "source": "robot_WheelLegActuator_c15691", "target": "robot_WheelLegActuator_MAX_TORQUE_NM_b7c10d", "type": "contains", "metadata": {}}, {"id": "e_robot_Wh_robot_Wh_contains", "source": "robot_WheelLegActuator_c15691", "target": "robot_WheelLegActuator___init___79ce68", "type": "contains", "metadata": {}}, {"id": "e_robot_Wh_robot_Wh_contains", "source": "robot_WheelLegActuator_c15691", "target": "robot_WheelLegActuator_set_torque_cf05b7", "type": "contains", "metadata": {}}, {"id": "e_robot_Wh_robot_Wh_contains", "source": "robot_WheelLegActuator_c15691", "target": "robot_WheelLegActuator__apply_torque_2515e3", "type": "contains", "metadata": {}}, {"id": "e_robot_Wh_robot_Wh_contains", "source": "robot_WheelLegActuator_c15691", "target": "robot_WheelLegActuator_step_5943e5", "type": "contains", "metadata": {}}, {"id": "e_robot_py_robot_Lo_contains", "source": "robot_py_3e0ed9", "target": "robot_LocomotionController_9d6ac0", "type": "contains", "metadata": {}}, {"id": "e_robot_Lo_robot_Lo_contains", "source": "robot_LocomotionController_9d6ac0", "target": "robot_LocomotionController___init___2d0ff7", "type": "contains", "metadata": {}}, {"id": "e_robot_Lo_robot_Lo_contains", "source": "robot_LocomotionController_9d6ac0", "target": "robot_LocomotionController_walk_946007", "type": "contains", "metadata": {}}, {"id": "e_robot_Lo_robot_Lo_contains", "source": "robot_LocomotionController_9d6ac0", "target": "robot_LocomotionController__compute_torq_fec2ad", "type": "contains", "metadata": {}}, {"id": "e_robot_Lo_robot_Lo_contains", "source": "robot_LocomotionController_9d6ac0", "target": "robot_LocomotionController_update_cbe0b1", "type": "contains", "metadata": {}}, {"id": "e_robot_Lo_robot_Lo_contains", "source": "robot_LocomotionController_9d6ac0", "target": "robot_LocomotionController__update_pose_9ca0c5", "type": "contains", "metadata": {}}, {"id": "e_robot_py_robot_YO_contains", "source": "robot_py_3e0ed9", "target": "robot_YOLODetector_9d4023", "type": "contains", "metadata": {}}, {"id": "e_robot_YO_robot_YO_contains", "source": "robot_YOLODetector_9d4023", "target": "robot_YOLODetector___init___ba1eb7", "type": "contains", "metadata": {}}, {"id": "e_robot_YO_robot_YO_contains", "source": "robot_YOLODetector_9d4023", "target": "robot_YOLODetector_load_b82b48", "type": "contains", "metadata": {}}, {"id": "e_robot_YO_robot_YO_contains", "source": "robot_YOLODetector_9d4023", "target": "robot_YOLODetector_detect_f44872", "type": "contains", "metadata": {}}, {"id": "e_robot_YO_robot_YO_contains", "source": "robot_YOLODetector_9d4023", "target": "robot_YOLODetector__run_inference_9eba26", "type": "contains", "metadata": {}}, {"id": "e_robot_YO_robot_YO_contains", "source": "robot_YOLODetector_9d4023", "target": "robot_YOLODetector__postprocess_c26522", "type": "contains", "metadata": {}}, {"id": "e_robot_py_robot_Ro_contains", "source": "robot_py_3e0ed9", "target": "robot_RobotBrain_893384", "type": "contains", "metadata": {}}, {"id": "e_robot_Ro_robot_Ro_contains", "source": "robot_RobotBrain_893384", "target": "robot_RobotBrain___init___5f1b6b", "type": "contains", "metadata": {}}, {"id": "e_robot_Ro_robot_Ro_contains", "source": "robot_RobotBrain_893384", "target": "robot_RobotBrain_run_20beec", "type": "contains", "metadata": {}}, {"id": "e_robot_Ro_robot_Ro_contains", "source": "robot_RobotBrain_893384", "target": "robot_RobotBrain__tick_f2f344", "type": "contains", "metadata": {}}, {"id": "e_robot_Ro_robot_Ro_contains", "source": "robot_RobotBrain_893384", "target": "robot_RobotBrain__react_c315da", "type": "contains", "metadata": {}}, {"id": "e_robot_Ro_robot_Ro_contains", "source": "robot_RobotBrain_893384", "target": "robot_RobotBrain_stop_51f993", "type": "contains", "metadata": {}}, {"id": "e_robot_py_robot_ma_contains", "source": "robot_py_3e0ed9", "target": "robot_main_4009b8", "type": "contains", "metadata": {}}]};

const NODE_COLORS = {
  module:    "#00c8ff",
  namespace: "#50ffcc",
  class:     "#ff50dc",
  struct:    "#ff8c3c",
  function:  "#50c850",
  method:    "#8cff50",
  variable:  "#c8a0ff",
  import:    "#ffdc28",
  lambda:    "#ff6464",
};
const EDGE_COLORS = {
  contains:    "#3c3c88",
  calls:       "#50ff50",
  inherits:    "#ff50dc",
  imports:     "#ffdc28",
  references:  "#64b4ff",
  instantiates:"#ff8c3c",
  overrides:   "#ff5050",
  uses_type:   "#b464ff",
};
const NODE_RADIUS = {
  module: 20, namespace: 16, class: 14, struct: 14,
  function: 10, method: 9, variable: 6, import: 7, lambda: 8,
};

function parseYamlLike(text) {
  // Accept JSON directly (from src2yaml --json or hand-crafted)
  // or the YAML structure (graph: nodes: edges:)
  try {
    const j = JSON.parse(text);
    if (j.graph) return { nodes: j.graph.nodes || [], edges: j.graph.edges || [] };
    if (j.nodes) return j;
  } catch {}
  // Minimal YAML→JSON: extract nodes/edges arrays by looking for JSON arrays
  // Proper approach: find the embedded JSON blobs in the pasted YAML
  const nodeMatch = text.match(/nodes:\s*(\[[\s\S]*?\])\s*edges:/);
  const edgeMatch = text.match(/edges:\s*(\[[\s\S]*?\])\s*$/);
  try {
    return {
      nodes: nodeMatch ? JSON.parse(nodeMatch[1]) : [],
      edges: edgeMatch ? JSON.parse(edgeMatch[1]) : [],
    };
  } catch { return null; }
}

export default function CodeGraph() {
  const svgRef = useRef(null);
  const simRef = useRef(null);
  const [graphData, setGraphData] = useState(SAMPLE_DATA);
  const [selected, setSelected] = useState(null);
  const [hovered, setHovered] = useState(null);
  const [activeNodeTypes, setActiveNodeTypes] = useState(new Set(Object.keys(NODE_COLORS)));
  const [activeEdgeTypes, setActiveEdgeTypes] = useState(new Set(Object.keys(EDGE_COLORS)));
  const [showImportPanel, setShowImportPanel] = useState(false);
  const [importText, setImportText] = useState("");
  const [importError, setImportError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [dims, setDims] = useState({ w: 900, h: 600 });

  const containerRef = useRef(null);
  useEffect(() => {
    const ro = new ResizeObserver(entries => {
      for (const e of entries) {
        setDims({ w: e.contentRect.width, h: e.contentRect.height });
      }
    });
    if (containerRef.current) ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  const visibleNodes = graphData.nodes.filter(n => activeNodeTypes.has(n.type));
  const visibleNodeIds = new Set(visibleNodes.map(n => n.id));
  const visibleEdges = graphData.edges.filter(
    e => activeEdgeTypes.has(e.type) && visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
  );

  // Highlight: selected node + its neighbors
  const highlightIds = new Set();
  const highlightEdgeIds = new Set();
  if (selected) {
    highlightIds.add(selected.id);
    visibleEdges.forEach(e => {
      if (e.source === selected.id || e.target === selected.id) {
        highlightIds.add(e.source);
        highlightIds.add(e.target);
        highlightEdgeIds.add(e.id);
      }
    });
  }
  if (hovered && !selected) {
    highlightIds.add(hovered);
    visibleEdges.forEach(e => {
      if (e.source === hovered || e.target === hovered) {
        highlightIds.add(e.source);
        highlightIds.add(e.target);
        highlightEdgeIds.add(e.id);
      }
    });
  }

  // Search highlight
  const searchIds = new Set();
  if (searchTerm.length > 1) {
    const q = searchTerm.toLowerCase();
    visibleNodes.forEach(n => {
      if (n.name.toLowerCase().includes(q) || n.qualified_name?.toLowerCase().includes(q)) {
        searchIds.add(n.id);
      }
    });
  }

  useEffect(() => {
    if (!svgRef.current || !dims.w) return;
    const { w, h } = dims;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Defs: arrowheads per edge type + glow filter
    const defs = svg.append("defs");
    defs.append("filter").attr("id", "glow")
      .append("feGaussianBlur").attr("stdDeviation", "3").attr("result", "coloredBlur");
    const feMerge = defs.select("filter#glow").append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    Object.entries(EDGE_COLORS).forEach(([type, color]) => {
      defs.append("marker")
        .attr("id", `arrow-${type}`)
        .attr("viewBox", "0 -4 8 8")
        .attr("refX", 8).attr("refY", 0)
        .attr("markerWidth", 6).attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-4L8,0L0,4")
        .attr("fill", color);
    });

    // Background grid
    const gridG = svg.append("g").attr("class", "grid");
    const gridSize = 50;
    for (let x = 0; x < w * 3; x += gridSize)
      gridG.append("line").attr("x1", x - w).attr("y1", -h).attr("x2", x - w).attr("y2", h * 3)
        .attr("stroke", "#1a1a2e").attr("stroke-width", 1);
    for (let y = 0; y < h * 3; y += gridSize)
      gridG.append("line").attr("x1", -w).attr("y1", y - h).attr("x2", w * 3).attr("y2", y - h)
        .attr("stroke", "#1a1a2e").attr("stroke-width", 1);

    const g = svg.append("g");

    // Zoom/pan
    const zoom = d3.zoom()
      .scaleExtent([0.1, 5])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
        gridG.attr("transform", event.transform);
      });
    svg.call(zoom);
    svg.on("click", (event) => {
      if (event.target === svgRef.current) setSelected(null);
    });

    // Build node/edge maps
    const nodeMap = {};
    visibleNodes.forEach(n => { nodeMap[n.id] = { ...n, x: w/2 + (Math.random()-0.5)*200, y: h/2 + (Math.random()-0.5)*200 }; });
    const simNodes = Object.values(nodeMap);
    const simEdges = visibleEdges.map(e => ({
      ...e,
      source: e.source,
      target: e.target,
    }));

    // Edges
    const edgeG = g.append("g").attr("class", "edges");
    const edgeSel = edgeG.selectAll("path")
      .data(simEdges, d => d.id)
      .join("path")
      .attr("stroke", d => EDGE_COLORS[d.type] || "#888")
      .attr("stroke-width", d => d.type === "inherits" ? 2.5 : d.type === "calls" ? 2 : 1.2)
      .attr("fill", "none")
      .attr("marker-end", d => `url(#arrow-${d.type})`)
      .attr("opacity", 0.7)
      .style("cursor", "default");

    // Nodes
    const nodeG = g.append("g").attr("class", "nodes");
    const nodeSel = nodeG.selectAll("g")
      .data(simNodes, d => d.id)
      .join("g")
      .attr("class", "node")
      .style("cursor", "pointer")
      .call(d3.drag()
        .on("start", (event, d) => {
          if (!event.active) sim.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
        .on("end", (event, d) => {
          if (!event.active) sim.alphaTarget(0);
          d.fx = null; d.fy = null;
        })
      )
      .on("click", (event, d) => {
        event.stopPropagation();
        setSelected(prev => prev?.id === d.id ? null : d);
      })
      .on("mouseenter", (_, d) => setHovered(d.id))
      .on("mouseleave", () => setHovered(null));

    // Glow ring
    nodeSel.append("circle")
      .attr("r", d => (NODE_RADIUS[d.type] || 8) + 6)
      .attr("fill", d => NODE_COLORS[d.type] || "#888")
      .attr("opacity", 0.15)
      .attr("filter", "url(#glow)");

    // Outer ring
    nodeSel.append("circle")
      .attr("r", d => NODE_RADIUS[d.type] || 8)
      .attr("fill", d => NODE_COLORS[d.type] || "#888")
      .attr("opacity", 0.9);

    // Inner dark fill
    nodeSel.append("circle")
      .attr("r", d => (NODE_RADIUS[d.type] || 8) - 3)
      .attr("fill", "#0a0a18")
      .attr("opacity", 0.85);

    // Inner dot
    nodeSel.append("circle")
      .attr("r", d => Math.max(2, (NODE_RADIUS[d.type] || 8) / 3))
      .attr("fill", d => NODE_COLORS[d.type] || "#888")
      .attr("opacity", 0.8);

    // Labels
    nodeSel.append("text")
      .attr("dy", d => (NODE_RADIUS[d.type] || 8) + 13)
      .attr("text-anchor", "middle")
      .attr("font-family", "monospace")
      .attr("font-size", d => ["module","class","namespace"].includes(d.type) ? 11 : 9)
      .attr("fill", d => NODE_COLORS[d.type] || "#aaa")
      .attr("opacity", 0.85)
      .attr("pointer-events", "none")
      .text(d => d.name.length > 18 ? d.name.slice(0, 16) + "…" : d.name);

    // Simulation
    const edgeLengths = { contains: 70, calls: 140, inherits: 120, imports: 90 };
    const sim = d3.forceSimulation(simNodes)
      .force("link", d3.forceLink(simEdges)
        .id(d => d.id)
        .distance(d => edgeLengths[d.type] || 110)
        .strength(d => d.type === "contains" ? 0.7 : 0.3))
      .force("charge", d3.forceManyBody().strength(-300).distanceMax(400))
      .force("center", d3.forceCenter(w / 2, h / 2).strength(0.05))
      .force("collision", d3.forceCollide(d => (NODE_RADIUS[d.type] || 8) + 14))
      .alphaDecay(0.015)
      .on("tick", () => {
        edgeSel.attr("d", d => {
          const s = d.source, t = d.target;
          if (!s || !t) return "";
          const dx = t.x - s.x, dy = t.y - s.y;
          const dist = Math.sqrt(dx*dx+dy*dy) || 1;
          const sr = (NODE_RADIUS[s.type] || 8);
          const tr = (NODE_RADIUS[t.type] || 8) + 10;
          const mx = (s.x + t.x)/2 - dy * 0.15;
          const my = (s.y + t.y)/2 + dx * 0.15;
          const x1 = s.x + (dx/dist)*sr, y1 = s.y + (dy/dist)*sr;
          const x2 = t.x - (dx/dist)*tr, y2 = t.y - (dy/dist)*tr;
          return `M${x1},${y1} Q${mx},${my} ${x2},${y2}`;
        });
        nodeSel.attr("transform", d => `translate(${d.x},${d.y})`);
      });

    simRef.current = sim;

    // Apply highlight/dim after render
    return () => sim.stop();
  }, [graphData, activeNodeTypes, activeEdgeTypes, dims]);

  // Highlight overlay — update without re-running sim
  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    const hasHL = highlightIds.size > 0;
    const hasSearch = searchIds.size > 0;

    svg.selectAll(".node").each(function(d) {
      const inHL = !hasHL || highlightIds.has(d.id);
      const inSearch = !hasSearch || searchIds.has(d.id);
      const opacity = (!inHL ? 0.12 : 1) * (!inSearch && hasSearch ? 0.2 : 1);
      d3.select(this).attr("opacity", opacity);
    });
    svg.selectAll(".edges path").each(function(d) {
      const inHL = !hasHL || highlightEdgeIds.has(d.id);
      d3.select(this).attr("opacity", inHL ? 0.85 : 0.06);
    });
  }, [highlightIds, highlightEdgeIds, searchIds]);

  const toggleNodeType = (t) => setActiveNodeTypes(prev => {
    const s = new Set(prev);
    s.has(t) ? s.delete(t) : s.add(t);
    return s;
  });
  const toggleEdgeType = (t) => setActiveEdgeTypes(prev => {
    const s = new Set(prev);
    s.has(t) ? s.delete(t) : s.add(t);
    return s;
  });

  const handleImport = () => {
    const parsed = parseYamlLike(importText);
    if (!parsed || !parsed.nodes) {
      setImportError("Could not parse. Paste JSON output from src2yaml, or a graph: { nodes: [], edges: [] } structure.");
      return;
    }
    setGraphData(parsed);
    setSelected(null);
    setImportError("");
    setShowImportPanel(false);
    setImportText("");
  };

  const selectedEdges = selected
    ? visibleEdges.filter(e => e.source === selected.id || e.target === selected.id)
    : [];

  return (
    <div style={{
      width: "100%", height: "100vh", background: "#080810",
      display: "flex", flexDirection: "column", fontFamily: "monospace",
      color: "#c8c8e8", overflow: "hidden",
    }}>
      {/* Top bar */}
      <div style={{
        display: "flex", alignItems: "center", gap: 12, padding: "6px 14px",
        background: "#0d0d20", borderBottom: "1px solid #1e1e3e",
        flexShrink: 0, flexWrap: "wrap",
      }}>
        <span style={{ color: "#00c8ff", fontWeight: "bold", fontSize: 13, letterSpacing: 2 }}>
          ⬡ CODEGRAPH
        </span>
        <span style={{ color: "#404060", fontSize: 11 }}>
          {visibleNodes.length}N / {visibleEdges.length}E
        </span>

        {/* Search */}
        <input
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          placeholder="search nodes…"
          style={{
            background: "#12122a", border: "1px solid #2a2a4a", color: "#c8c8e8",
            padding: "3px 8px", fontSize: 11, borderRadius: 3, width: 160,
            outline: "none",
          }}
        />

        {/* Node type filters */}
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {Object.entries(NODE_COLORS).map(([t, c]) => (
            <button key={t} onClick={() => toggleNodeType(t)} style={{
              background: activeNodeTypes.has(t) ? c + "22" : "#0a0a18",
              border: `1px solid ${activeNodeTypes.has(t) ? c : "#2a2a3a"}`,
              color: activeNodeTypes.has(t) ? c : "#404060",
              padding: "2px 7px", fontSize: 10, borderRadius: 2, cursor: "pointer",
              transition: "all 0.15s",
            }}>{t}</button>
          ))}
        </div>

        {/* Edge type filters */}
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {Object.entries(EDGE_COLORS).map(([t, c]) => (
            <button key={t} onClick={() => toggleEdgeType(t)} style={{
              background: activeEdgeTypes.has(t) ? c + "22" : "#0a0a18",
              border: `1px solid ${activeEdgeTypes.has(t) ? c : "#2a2a3a"}`,
              color: activeEdgeTypes.has(t) ? c : "#404060",
              padding: "2px 7px", fontSize: 10, borderRadius: 2, cursor: "pointer",
              transition: "all 0.15s",
            }}>─ {t}</button>
          ))}
        </div>

        <button onClick={() => setShowImportPanel(p => !p)} style={{
          marginLeft: "auto", background: "#1a1a3a", border: "1px solid #3a3a6a",
          color: "#8080c8", padding: "3px 10px", fontSize: 11, borderRadius: 3,
          cursor: "pointer",
        }}>⊕ Import YAML/JSON</button>
      </div>

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Graph canvas */}
        <div ref={containerRef} style={{ flex: 1, position: "relative", overflow: "hidden" }}>
          <svg ref={svgRef} width={dims.w} height={dims.h}
            style={{ display: "block", background: "transparent" }} />

          {/* Hint */}
          <div style={{
            position: "absolute", bottom: 10, left: 12,
            fontSize: 10, color: "#2a2a5a", pointerEvents: "none",
          }}>
            scroll: zoom · drag: pan · drag node: move · click node: inspect
          </div>
        </div>

        {/* Inspector panel */}
        {selected && (
          <div style={{
            width: 280, background: "#0d0d20", borderLeft: "1px solid #1e1e3e",
            padding: 14, overflowY: "auto", flexShrink: 0, fontSize: 11,
          }}>
            <div style={{
              color: NODE_COLORS[selected.type] || "#aaa",
              fontSize: 13, fontWeight: "bold", marginBottom: 8,
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <span>◈ {selected.name}</span>
              <button onClick={() => setSelected(null)} style={{
                background: "none", border: "none", color: "#404060",
                cursor: "pointer", fontSize: 16,
              }}>×</button>
            </div>

            <Row label="type" value={selected.type} color={NODE_COLORS[selected.type]} />
            <Row label="qualified" value={selected.qualified_name} />
            <Row label="language" value={selected.language} />
            {selected.loc && <>
              <Row label="file" value={selected.loc.file} />
              <Row label="lines" value={`${selected.loc.line_start}–${selected.loc.line_end}`} />
            </>}

            {/* Metadata */}
            {selected.metadata && Object.entries(selected.metadata).map(([k, v]) => {
              if (v === null || v === undefined) return null;
              const display = Array.isArray(v)
                ? (v.length === 0 ? "[]"
                  : v.map(p => typeof p === "object" ? `${p.name}${p.type ? `:${p.type}` : ""}` : String(p)).join(", "))
                : String(v);
              if (!display || display === "false") return null;
              return <Row key={k} label={k} value={display} />;
            })}

            {/* Edges */}
            {selectedEdges.length > 0 && (
              <div style={{ marginTop: 12, borderTop: "1px solid #1e1e3e", paddingTop: 8 }}>
                <div style={{ color: "#404080", fontSize: 10, marginBottom: 6 }}>EDGES ({selectedEdges.length})</div>
                {selectedEdges.map((e, i) => {
                  const isOut = e.source === selected.id;
                  const otherId = isOut ? e.target : e.source;
                  const other = graphData.nodes.find(n => n.id === otherId);
                  return (
                    <div key={i} style={{
                      display: "flex", alignItems: "center", gap: 6,
                      marginBottom: 4, cursor: "pointer",
                    }} onClick={() => {
                      const n = graphData.nodes.find(n => n.id === otherId);
                      if (n) setSelected(n);
                    }}>
                      <span style={{ color: EDGE_COLORS[e.type] || "#888", fontSize: 10, minWidth: 70 }}>
                        {isOut ? "→" : "←"} {e.type}
                      </span>
                      <span style={{
                        color: NODE_COLORS[other?.type] || "#aaa",
                        overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                      }}>
                        {other?.name || otherId.slice(0, 12)}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Import panel */}
      {showImportPanel && (
        <div style={{
          position: "absolute", top: 48, right: 0,
          width: 460, background: "#0d0d22", border: "1px solid #2a2a5a",
          padding: 16, zIndex: 100, borderRadius: "0 0 0 6px",
        }}>
          <div style={{ color: "#8080c8", fontSize: 12, marginBottom: 8 }}>
            Paste JSON from <code style={{color:"#50ffcc"}}>src2yaml</code> output or a <code style={{color:"#50ffcc"}}>{"{"}"graph": {"{"}"nodes":[...],"edges":[...]{"}"}{"}"}}</code> block:
          </div>
          <textarea
            value={importText}
            onChange={e => setImportText(e.target.value)}
            rows={10}
            style={{
              width: "100%", background: "#080818", border: "1px solid #2a2a4a",
              color: "#c8c8e8", fontSize: 10, fontFamily: "monospace",
              padding: 8, resize: "vertical", boxSizing: "border-box",
            }}
            placeholder='{"graph": {"nodes": [...], "edges": [...]}}'
          />
          {importError && <div style={{ color: "#ff5050", fontSize: 10, marginTop: 4 }}>{importError}</div>}
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <button onClick={handleImport} style={{
              background: "#1a2a4a", border: "1px solid #3a5a8a", color: "#64b4ff",
              padding: "5px 16px", fontSize: 11, cursor: "pointer", borderRadius: 3,
            }}>Load Graph</button>
            <button onClick={() => { setShowImportPanel(false); setImportError(""); }} style={{
              background: "#1a1a2a", border: "1px solid #2a2a4a", color: "#606080",
              padding: "5px 16px", fontSize: 11, cursor: "pointer", borderRadius: 3,
            }}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ label, value, color }) {
  return (
    <div style={{ display: "flex", gap: 6, marginBottom: 4, lineHeight: 1.4 }}>
      <span style={{ color: "#404070", minWidth: 72, flexShrink: 0 }}>{label}</span>
      <span style={{
        color: color || "#9090c0", wordBreak: "break-all",
        overflow: "hidden", textOverflow: "ellipsis",
      }}>{value}</span>
    </div>
  );
}
