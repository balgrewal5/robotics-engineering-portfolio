# ROS 2 Robot Arm Kinematics, Simulation and Control

A simulation-based 2-DOF robotic manipulator developed using ROS 2, Gazebo, RViz and `ros2_control`. The project combines robot modelling, kinematics, trajectory control, simulation, joint-state feedback and ROS 2 system integration into a reproducible robotics control system.

![ROS 2 Robot Arm in Gazebo and RViz](media/project-2-gazebo-rviz.png)

## Overview

This project was developed to connect robot kinematics theory with a complete ROS 2 simulation and control workflow.

A custom 2-DOF planar robot arm was modelled in URDF and simulated in Gazebo. The joints are controlled through `ros2_control` using a `JointTrajectoryController`, while joint-state feedback is published through a `JointStateBroadcaster`.

`robot_state_publisher` converts the measured joint states into TF transforms so the same simulated motion can be visualised in RViz.

A custom ROS 2 Python node was also developed to solve inverse kinematics for Cartesian end-effector targets and automatically convert the resulting joint angles into ROS 2 trajectory commands.

The complete project can be launched using a single ROS 2 launch file.

---

## Key Features

- Custom 2-DOF robotic arm model in URDF
- Revolute joint modelling and joint limits
- Visual, collision and inertial robot properties
- Gazebo physics simulation
- `gz_ros2_control` simulation interface
- `ros2_control` position command interfaces
- `JointStateBroadcaster`
- `JointTrajectoryController`
- Joint position and velocity feedback
- Multi-point joint trajectory execution
- ROS 2 `FollowJointTrajectory` action interface
- Robot TF tree generated using `robot_state_publisher`
- RViz visualisation of simulated joint motion
- Gazebo simulation clock integration using `/clock`
- Forward and inverse kinematics
- Jacobian analysis and singularity understanding
- Custom inverse-kinematics ROS 2 node
- One-command integrated ROS 2 launch system

---

## System Architecture

```mermaid
flowchart TD

    A["Cartesian Target (x, y)"] --> B["Inverse Kinematics Node"]
    B --> C["Joint Angles: theta1, theta2"]
    C --> D["JointTrajectory Message"]
    D --> E["JointTrajectoryController"]
    E --> F["ros2_control"]
    F --> G["gz_ros2_control"]
    G --> H["Gazebo Simulated Joints"]

    H --> I["Joint State Interfaces"]
    I --> J["JointStateBroadcaster"]
    J --> K["/joint_states"]
    K --> L["robot_state_publisher"]
    L --> M["TF"]
    M --> N["RViz"]

    H --> O["Gazebo Visualisation"]

    L --> M["TF"]

    M --> N["RViz"]

    H --> O["Gazebo Visualisation"]
 
