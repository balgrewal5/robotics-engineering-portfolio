import math

import rclpy
from rclpy.node import Node

from trajectory_msgs.msg import JointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration


class ArmIKDemo(Node):

    def __init__(self):
        super().__init__('arm_ik_demo')

        # Link lengths
        self.L1 = 1.0
        self.L2 = 1.0

        # Publish trajectories to the ros2_control arm controller
        self.publisher = self.create_publisher(
            JointTrajectory,
            '/arm_controller/joint_trajectory',
            10
        )

        # Cartesian end-effector targets
        self.targets = [
            (1.0, 1.0),
            (0.5, 1.5),
            (1.5, 0.5),
            (2.0, 0.0)
        ]

        self.target_index = 0

        # Move to a new target every 4 seconds
        self.timer = self.create_timer(
            4.0,
            self.move_to_next_target
        )

        self.get_logger().info(
            '2-DOF inverse kinematics demo started'
        )

    def inverse_kinematics(self, x, y):

        # Solve for theta2
        cos_theta2 = (
            x**2
            + y**2
            - self.L1**2
            - self.L2**2
        ) / (
            2 * self.L1 * self.L2
        )

        # Check whether the target is reachable
        if cos_theta2 < -1.0 or cos_theta2 > 1.0:
            return None

        theta2 = math.acos(cos_theta2)

        # Solve for theta1
        theta1 = (
            math.atan2(y, x)
            - math.atan2(
                self.L2 * math.sin(theta2),
                self.L1 + self.L2 * math.cos(theta2)
            )
        )

        return theta1, theta2

    def move_to_next_target(self):

        x, y = self.targets[self.target_index]

        solution = self.inverse_kinematics(x, y)

        if solution is None:
            self.get_logger().warning(
                f'Target ({x:.2f}, {y:.2f}) is unreachable'
            )

        else:
            theta1, theta2 = solution

            trajectory = JointTrajectory()

            trajectory.joint_names = [
                'joint1',
                'joint2'
            ]

            point = JointTrajectoryPoint()

            point.positions = [
                theta1,
                theta2
            ]

            point.time_from_start = Duration(
                sec=3,
                nanosec=0
            )

            trajectory.points.append(point)

            self.publisher.publish(trajectory)

            self.get_logger().info(
                f'Target ({x:.2f}, {y:.2f}) -> '
                f'theta1={theta1:.2f} rad, '
                f'theta2={theta2:.2f} rad'
            )

        # Move to next Cartesian target
        self.target_index += 1

        if self.target_index >= len(self.targets):
            self.target_index = 0


def main(args=None):

    rclpy.init(args=args)

    node = ArmIKDemo()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
