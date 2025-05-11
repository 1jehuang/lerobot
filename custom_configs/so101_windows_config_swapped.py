# Modified configuration for SO-101 on Windows with SWAPPED ports
from dataclasses import dataclass, field
from lerobot.common.robot_devices.robots.configs import RobotConfig, ManipulatorRobotConfig
from lerobot.common.robot_devices.cameras.configs import OpenCVCameraConfig, CameraConfig
from lerobot.common.robot_devices.motors.configs import FeetechMotorsBusConfig, MotorsBusConfig

@RobotConfig.register_subclass("so101_windows_swapped")
@dataclass
class So101WindowsSwappedRobotConfig(ManipulatorRobotConfig):
    calibration_dir: str = ".cache/calibration/so101_windows_swapped"
    max_relative_target: int | None = None

    leader_arms: dict[str, MotorsBusConfig] = field(
        default_factory=lambda: {
            "main": FeetechMotorsBusConfig(
                # SWAPPED: Now using COM4 for the leader arm 
                port="COM4",  
                motors={
                    # name: (index, model)
                    "shoulder_pan": [1, "sts3215"],
                    "shoulder_lift": [2, "sts3215"],
                    "elbow_flex": [3, "sts3215"],
                    "wrist_flex": [4, "sts3215"],
                    "wrist_roll": [5, "sts3215"],
                    "gripper": [6, "sts3215"],
                },
            ),
        }
    )

    follower_arms: dict[str, MotorsBusConfig] = field(
        default_factory=lambda: {
            "main": FeetechMotorsBusConfig(
                # SWAPPED: Now using COM3 for the follower arm
                port="COM3",  
                motors={
                    # name: (index, model)
                    "shoulder_pan": [1, "sts3215"],
                    "shoulder_lift": [2, "sts3215"],
                    "elbow_flex": [3, "sts3215"],
                    "wrist_flex": [4, "sts3215"],
                    "wrist_roll": [5, "sts3215"],
                    "gripper": [6, "sts3215"],
                },
            ),
        }
    )

    cameras: dict[str, CameraConfig] = field(
        default_factory=lambda: {
            "laptop": OpenCVCameraConfig(
                camera_index=0,
                fps=30,
                width=640,
                height=480,
            ),
        }
    )

    mock: bool = False