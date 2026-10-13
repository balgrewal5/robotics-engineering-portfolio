import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # Package paths
    package_name = 'ros2_robot_arm'

    package_share = get_package_share_directory(package_name)

    urdf_path = os.path.join(
        package_share,
        'urdf',
        'two_dof_arm.urdf'
    )

    controller_config = os.path.join(
        package_share,
        'config',
        'arm_controllers.yaml'
    )

    # Read robot URDF
    with open(urdf_path, 'r') as urdf_file:
        robot_description = urdf_file.read()

    # Replace development-machine controller path with
    # the installed package controller configuration
    robot_description = robot_description.replace(
        '$(find my_first_ros_package)/config/arm_controllers.yaml',
        controller_config
    )

    # -------------------------
    # Gazebo
    # -------------------------

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            )
        ),
        launch_arguments={
            'gz_args': '-r empty.sdf'
        }.items()
    )

    # -------------------------
    # Gazebo simulation clock
    # -------------------------

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
        ],
        output='screen'
    )

    # -------------------------
    # Robot state publisher
    # -------------------------

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {
                'robot_description': robot_description,
                'use_sim_time': True,
                'ignore_timestamp': True
            }
        ]
    )

    # -------------------------
    # Spawn robot in Gazebo
    # -------------------------

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-world',
            'empty',
            '-topic',
            'robot_description',
            '-name',
            'two_dof_arm'
        ],
        output='screen'
    )

    # -------------------------
    # ros2_control controllers
    # -------------------------

    joint_state_broadcaster = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=[
                    'joint_state_broadcaster',
                    '--controller-manager',
                    '/controller_manager',
                    '--controller-manager-timeout',
                    '60'
                ],
                output='screen'
            )
        ]
    )

    arm_controller = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=[
                    'arm_controller',
                    '--controller-manager',
                    '/controller_manager',
                    '--controller-manager-timeout',
                    '60'
                ],
                output='screen'
            )
        ]
    )

    # -------------------------
    # RViz
    # -------------------------

    rviz = TimerAction(
        period=8.0,
        actions=[
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz',
                output='screen',
                parameters=[
                    {'use_sim_time': True}
                ]
            )
        ]
    )

    return LaunchDescription([
        gazebo,
        clock_bridge,
        robot_state_publisher,
        spawn_robot,
        joint_state_broadcaster,
        arm_controller,
        rviz
    ])
