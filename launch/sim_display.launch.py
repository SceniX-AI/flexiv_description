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
    use_joint_pub_gui = LaunchConfiguration("use_joint_pub_gui")
    rvizconfig_launch_arg = LaunchConfiguration("rvizconfig")

    load_gripper = LaunchConfiguration("load_gripper").perform(context)
    gripper_name = LaunchConfiguration("gripper_name").perform(context)

    robot_name = LaunchConfiguration("robot_name").perform(context)

    base_xyz = LaunchConfiguration("base_xyz").perform(context)
    base_rpy = LaunchConfiguration("base_rpy").perform(context)

    camera_xyz = LaunchConfiguration("camera_xyz").perform(context)
    camera_rpy = LaunchConfiguration("camera_rpy").perform(context)

    top_cam_pos = [
        str(1.1938113941783666),
        str(-0.22467823828124378),
        str(0.46803932490384265),
        str(-2.437817414804678),
        str(-0.15175449927159113),
        str(1.1165512066044632),
    ]

    robot_joint_state_publish_frequency = LaunchConfiguration("robot_joint_state_publish_frequency")

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([FindPackageShare("flexiv_description"), "urdf", "rizon4s.urdf.xacro"]),
            " ",
            f"load_gripper:={load_gripper} ",
            f"gripper_name:={gripper_name} ",
            f"robot_name:=/flexiv/{robot_name} ",
            f'base_xyz:="{base_xyz}" ',
            f'base_rpy:="{base_rpy}" ',
            f'camera_xyz:="{camera_xyz}" ',
            f'camera_rpy:="{camera_rpy}" ',
        ]
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace=f"/flexiv/{robot_name}",
        parameters=[
            {
                "robot_description": ParameterValue(robot_description_content, value_type=str),
                "publish_frequency": ParameterValue(robot_joint_state_publish_frequency, value_type=float),
            },
        ],
        # remappings=[]
        # if IfCondition(use_joint_pub_gui).evaluate(context)
        # else [(f"/flexiv/{robot_name}/joint_states", f"/flexiv/{robot_name}/present_joint_states")],
        output={"both": "screen"},
    )

    joint_state_publisher_node = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        namespace=f"/flexiv/{robot_name}",
        # remappings=[]
        # if UnlessCondition(use_joint_pub_gui).evaluate(context)
        # else [(f"/flexiv/{robot_name}/joint_states", f"/flexiv/{robot_name}/present_joint_states")],
        parameters=[{"source_list": [f"/flexiv/{robot_name}/present_joint_states"]}],
    )

    joint_state_publisher_gui_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        namespace=f"/flexiv/{robot_name}",
        condition=IfCondition(use_joint_pub_gui),
        output={"both": "screen"},
    )

    rviz2_node = Node(
        condition=IfCondition(use_rviz_launch_arg),
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rvizconfig_launch_arg],
        output={"both": "screen"},
    )

    static_tf_top_cam_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        namespace="topcam",
        name="static_tf_world_to_top_cam",
        arguments=[
            "--x",
            top_cam_pos[0],
            "--y",
            top_cam_pos[1],
            "--z",
            top_cam_pos[2],
            "--roll",
            top_cam_pos[3],
            "--pitch",
            top_cam_pos[4],
            "--yaw",
            top_cam_pos[5],
            "--frame-id",
            "world",
            "--child-frame-id",
            "top_cam",
        ],
        output="screen",
    )

    return [
        robot_state_publisher_node,
        joint_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz2_node,
        static_tf_top_cam_node,
    ]


def generate_launch_description():
    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "use_rviz", default_value="true", choices=("true", "false"), description="launches RViz if set to `true`."
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "rvizconfig",
            default_value=PathJoinSubstitution([FindPackageShare("flexiv_description"), "rviz", "view_rizon4s.rviz"]),
            description="file path to the config file RViz should load.",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "use_joint_pub_gui",
            default_value="false",
            choices=("true", "false"),
            description="launches the joint_state_publisher GUI.",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "robot_joint_state_publish_frequency",
            default_value="50.0",
            description="TF publish frequency for robot_state_publisher (Hz)",
        )
    )

    declared_arguments.append(DeclareLaunchArgument("robot_name", default_value="arm"))

    declared_arguments.append(DeclareLaunchArgument("base_xyz", default_value="0 0 0"))
    declared_arguments.append(DeclareLaunchArgument("base_rpy", default_value="0 0 0"))
    declared_arguments.append(DeclareLaunchArgument("camera_xyz", default_value="-0.08 0.0 0.05"))
    declared_arguments.append(DeclareLaunchArgument("camera_rpy", default_value="-0.17453293 0.0 -1.57079633"))

    declared_arguments.append(
        DeclareLaunchArgument(
            name="load_gripper", default_value="True", description="Flag to load the Flexiv Grav gripper"
        ),
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            name="gripper_name", default_value="Flexiv-GN01", description="Full name of the gripper to be controlled"
        ),
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time", default_value="true", choices=("true", "false"), description="Use simulated time"
        )
    )

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
