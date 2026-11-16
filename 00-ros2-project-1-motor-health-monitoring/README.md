# ROS 2 Project 1 — Motor Health Monitoring System

A ROS 2 Python application that simulates motor temperature monitoring using publishers, subscribers, parameters, QoS, services, launch files, logging, and automated testing.

## Overview

The system publishes simulated motor temperature readings and monitors them against a configurable warning threshold.

The threshold can be changed while the system is running using ROS 2 parameters. A service can reset it to its default value.

Example:

```text
Temperature: 47.8 °C
Threshold:   45.0 °C
→ MOTOR HOT
```

Changing the threshold to `50.0` immediately changes the result to:

```text
→ Motor normal
```

## Key Features

- ROS 2 Python publisher and subscriber
- `std_msgs/msg/Float64` temperature messages
- Runtime-configurable `warning_threshold` parameter
- `warning_enabled` parameter
- Reset service using `std_srvs/srv/Trigger`
- Custom QoS configuration
- Python launch file
- Namespaces and topic remapping
- ROS 2 logging
- Separated decision logic for unit testing
- `pytest` and `colcon test`

## Architecture

```text
Temperature Publisher
        │
        │ /robot1/motor_temperature
        ▼
Temperature Subscriber
        │
        ├── warning_threshold
        ├── warning_enabled
        ├── temperature decision logic
        └── reset_warning_threshold service
```

## Running the System

Build the package:

```bash
colcon build --packages-select python_temperature_monitor
source install/setup.bash
```

Launch:

```bash
ros2 launch python_temperature_monitor temperature_system.launch.py
```

Change the threshold at runtime:

```bash
ros2 param set /robot1/temperature_subscriber warning_threshold 50.0
```

Reset the threshold:

```bash
ros2 service call /reset_warning_threshold std_srvs/srv/Trigger
```

## Testing

The temperature decision logic is separated from the ROS communication layer so it can be tested independently.

```python
def check_temperature(temperature, threshold):
    if temperature > threshold:
        return 'HOT'
    return 'NORMAL'
```

Run the unit tests:

```bash
python3 -m pytest test/test_temperature_logic.py -q
```

Run the full package test suite:

```bash
colcon test --packages-select python_temperature_monitor
colcon test-result --verbose
```

Final result:

```text
5 tests
0 errors
0 failures
1 skipped
```

## ROS 2 Concepts Demonstrated

- Nodes
- Publishers and subscribers
- Topics and message types
- Parameters
- Services
- QoS
- Launch files
- Namespaces and remapping
- Logging and CLI debugging
- Unit and package testing

## Technologies

ROS 2 Jazzy · Python · `rclpy` · Ubuntu 24.04 · WSL2 · `pytest` · `colcon`
