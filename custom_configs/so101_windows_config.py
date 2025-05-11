# Modified configuration for SO-101 on Windows
from dataclasses import dataclass, field
from lerobot.common.robot_devices.robots.configs import RobotConfig, ManipulatorRobotConfig
from lerobot.common.robot_devices.cameras.configs import OpenCVCameraConfig, CameraConfig
from lerobot.common.robot_devices.motors.configs import FeetechMotorsBusConfig, MotorsBusConfig

@RobotConfig.register_subclass("so101_windows")
@dataclass
class So101WindowsRobotConfig(ManipulatorRobotConfig):
    calibration_dir: str = ".cache/calibration/so101_windows"
    # `max_relative_target` limits the magnitude of the relative positional target vector for safety purposes.
    # Set this to a positive scalar to have the same value for all motors, or a list that is the same length as
    # the number of motors in your follower arms.
    max_relative_target: int | None = None

    leader_arms: dict[str, MotorsBusConfig] = field(
        default_factory=lambda: {
            "main": FeetechMotorsBusConfig(
                # On Windows, we need to use COM ports
                port="COM3",  # USB-Enhanced-SERIAL CH343 (COM3)
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
                # On Windows, we need to use COM ports
                port="COM4",  # USB-Enhanced-SERIAL CH343 (COM4)
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
                camera_index=0,  # This is typically the built-in webcam
                fps=30,
                width=640,
                height=480,
            ),
            # If you have a second camera, you can uncomment and use this
            # "external": OpenCVCameraConfig(
            #     camera_index=1,
            #     fps=30,
            #     width=640,
            #     height=480,
            # ),
        }
    )

    mock: bool = False
