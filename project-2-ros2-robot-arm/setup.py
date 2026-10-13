import os
from glob import glob

from setuptools import setup


package_name = 'ros2_robot_arm'


setup(
    name=package_name,
    version='0.0.1',

    py_modules=[
        'arm_ik_demo'
    ],

    package_dir={
        '': 'src'
    },

    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),

        (
            'share/' + package_name,
            ['package.xml']
        ),

        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')
        ),

        (
            os.path.join('share', package_name, 'urdf'),
            glob('urdf/*.urdf')
        ),

        (
            os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')
        ),
    ],

    install_requires=[
        'setuptools'
    ],

    zip_safe=True,

    maintainer='Balraj Grewal',

    description=(
        'ROS 2 2-DOF robot arm kinematics, '
        'simulation and control project.'
    ),

    license='MIT',

    entry_points={
        'console_scripts': [
            'arm_ik_demo = arm_ik_demo:main',
        ],
    },
)
