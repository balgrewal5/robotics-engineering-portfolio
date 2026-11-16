import rclpy
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy)
from std_msgs.msg import Float64


class TemperaturePublisher(Node):

    def __init__(self):
        super().__init__('python_temperature_publisher')

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.publisher_ = self.create_publisher(
            Float64,
            '/motor_temperature',
            qos_profile
        )

        self.timer = self.create_timer(
            1.0,
            self.timer_callback
        )

    def timer_callback(self):
        msg = Float64()
        msg.data = 47.8
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing temperature: {msg.data}')


def main(args=None):
    rclpy.init(args=args)

    node = TemperaturePublisher()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()
