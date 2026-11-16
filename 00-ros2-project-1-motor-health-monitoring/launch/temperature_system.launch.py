from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    warning_threshold = LaunchConfiguration('warning_threshold')

    return LaunchDescription([
        DeclareLaunchArgument(
            'warning_threshold',
            default_value='45.0'
        ),

        Node(
            package='python_temperature_monitor',
            executable='temperature_publisher',
            name='temperature_publisher',
            namespace='robot1',
            remappings=[
                ('/motor_temperature', '/robot1/motor_temperature')
            ]
        ),

        Node(
            package='python_temperature_monitor',
            executable='temperature_subscriber',
            name='temperature_subscriber',
            namespace='robot1',
            remappings=[
                 ('/motor_temperature', '/robot1/motor_temperature')
            ],
            parameters=[
                {'warning_threshold': warning_threshold}
            ]
        ),

    ])
