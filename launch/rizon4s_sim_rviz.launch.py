from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    use_rviz_launch_arg = LaunchConfiguration("use_rviz")
    use_joint_pub_launch_arg = LaunchConfiguration("use_joint_pub")
    use_joint_pub_gui_launch_arg = LaunchConfiguration("use_joint_pub_gui")
    rvizconfig_launch_arg = LaunchConfiguration("rvizconfig")
    remap_joint_states = LaunchConfiguration("remap_joint_states").perform(context).lower() == "true"

    arm_side = LaunchConfiguration("arm_side").perform(context)

    # base_xyz = LaunchConfiguration("base_xyz").perform(context)
    # base_rpy = LaunchConfiguration("base_rpy").perform(context)

    # camera_xyz = LaunchConfiguration("camera_xyz").perform(context)
    # camera_rpy = LaunchConfiguration("camera_rpy").perform(context)

    robot_joint_state_publish_frequency = LaunchConfiguration("robot_joint_state_publish_frequency")
    robot_sn = LaunchConfiguration("robot_sn")
    rizon_type = LaunchConfiguration("rizon_type")

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([FindPackageShare("flexiv_description"), "urdf", "rizon.urdf.xacro"]),
            " ",
            "rizon_type:=",
            rizon_type,
            " ",
            "robot_sn:=",
            robot_sn,
            " ",
            "load_gripper:=",
            "True",
            " ",
            "gripper_name:=",
            "Grav",
        ],
    )

    # Robot state publisher
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace=arm_side,
        parameters=[
            {"robot_description": ParameterValue(robot_description_content, value_type=str)},
            {"publish_frequency": ParameterValue(robot_joint_state_publish_frequency, value_type=float)},
        ],
        output={"both": "screen"},
    )

    joint_state_publisher_node = Node(
        condition=IfCondition(use_joint_pub_launch_arg),
        package="joint_state_publisher",
        executable="joint_state_publisher",
        namespace=arm_side,
        output={"both": "screen"},
    )

    joint_pub_gui_node_args = {
        "condition": IfCondition(use_joint_pub_gui_launch_arg),
        "package": "joint_state_publisher_gui",
        "executable": "joint_state_publisher_gui",
        "namespace": arm_side,
        "output": {"both": "screen"},
    }

    if remap_joint_states:
        joint_pub_gui_node_args["remappings"] = [
            (f"/{arm_side}/joint_states", f"/flexiv/{arm_side}/goal_joint_states"),
        ]

    joint_state_publisher_gui_node = Node(**joint_pub_gui_node_args)

    rviz2_node = Node(
        condition=IfCondition(use_rviz_launch_arg),
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=[
            "-d",
            rvizconfig_launch_arg,
        ],
        output={"both": "screen"},
    )

    return [
        robot_state_publisher_node,
        joint_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz2_node,
    ]


def generate_launch_description():
    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "use_rviz",
            default_value="true",
            choices=("true", "false"),
            description="launches RViz if set to `true`.",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "rvizconfig",
            default_value=PathJoinSubstitution([FindPackageShare("flexiv_description"), "rviz", "view_rizon.rviz"]),
            description="Absolute path to rviz config file.",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "use_joint_pub",
            default_value="false",
            choices=("true", "false"),
            description="launches the joint_state_publisher node.",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "use_joint_pub_gui",
            default_value="true",
            choices=("true", "false"),
            description="launches the joint_state_publisher GUI.",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "arm_side",
            default_value="",
            choices=("", "main"),
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "remap_joint_states",
            default_value="false",
            choices=("true", "false"),
            description="remaps the joint_states topic to the goal_joint_states topic.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "robot_joint_state_publish_frequency",
            default_value="20.0",
            description="TF publish frequency for robot_state_publisher (Hz)",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            name="rizon_type",
            default_value="Rizon4s",
            description="Type of the Flexiv Rizon robot.",
            choices=[
                "Rizon4",
                "Rizon4s",
                "Rizon10",
            ],
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            name="robot_sn",
            default_value="Rizon4s-sim",
            description="Serial number of the robot. Used to create a unique world frame.",
        )
    )
    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
