# Encoder-Feedback Differential-Drive Mobile Robot

![Robot Overview](media/robot-overview.jpg)

## Overview

This project is an autonomous differential-drive mobile robot developed to explore embedded control, sensor integration, and mobile-robot motion.

The robot uses quadrature wheel encoders for feedback, independent PI wheel-speed control, differential-drive kinematics, and encoder-based odometry. An HC-SR04 ultrasonic sensor detects nearby obstacles, while an MPU6050 provides accelerometer and gyroscope measurements.

During autonomous operation, the robot drives forward under closed-loop wheel-speed control, detects an obstacle at approximately 20 cm, stops, performs an encoder-measured ~90° avoidance turn, and continues driving.

## Demo

![Obstacle Avoidance Demo](media/obstacle-avoidance-demo.gif)

## Key Features

- Dual quadrature encoder feedback for left and right wheel motion
- Independent PI wheel-speed control
- Differential-drive kinematics
- Encoder-based odometry estimating position and heading
- HC-SR04 ultrasonic obstacle detection
- MPU6050 accelerometer and gyroscope integration
- Autonomous obstacle-response behaviour
- Encoder-measured approximately 90° turning
- Real-time serial monitoring of RPM, pose and sensor data

## Hardware

- Arduino Uno R3
- L298N dual H-bridge motor driver
- 2 × geared DC motors with quadrature encoders
- HC-SR04 ultrasonic distance sensor
- MPU6050 accelerometer and gyroscope
- 2-wheel differential-drive chassis with passive caster
- 65 mm wheels
- AA battery pack for motor power
- Separate Arduino power supply for untethered operation

## Robot Parameters

| Parameter | Value |
|---|---:|
| Wheel diameter | 65 mm |
| Wheel radius, \(r\) | 0.0325 m |
| Wheelbase, \(L\) | 0.13 m |
| Encoder resolution | ~960 counts/rev |
| PI speed target | 20 RPM |
| Obstacle threshold | ~20 cm |
| Avoidance turn | ~90° |

## System Architecture

```mermaid
flowchart LR

    US[HC-SR04<br/>Ultrasonic Sensor]
    IMU[MPU6050<br/>Accelerometer + Gyroscope]
    ENC_L[Left Wheel Encoder]
    ENC_R[Right Wheel Encoder]

    MCU[Arduino Uno<br/>Control + Odometry]

    DRIVER[L298N<br/>Motor Driver]

    LM[Left Motor]
    RM[Right Motor]

    US --> MCU
    IMU --> MCU
    ENC_L --> MCU
    ENC_R --> MCU

    MCU -->|PWM + Direction| DRIVER

    DRIVER --> LM
    DRIVER --> RM

    LM --> ENC_L
    RM --> ENC_R
