import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy)
from std_msgs.msg import Float64
from std_srvs.srv import Trigger


class TemperatureSubscriber(Node):

    def __init__(self):
        super().__init__('python_temperature_subscriber')

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.subscription = self.create_subscription(
            Float64,
            '/motor_temperature',
            self.temperature_callback,
            qos_profile
        )

        self.declare_parameter('warning_threshold', 45.0)
        self.declare_parameter('warning_enabled', True)

        self.reset_service = self.create_service(
            Trigger,
            '/reset_warning_threshold',
            self.reset_threshold_callback
        )

    def temperature_callback(self, msg):

        threshold = self.get_parameter(
            'warning_threshold'
        ).value

        warning_enabled = self.get_parameter(
            'warning_enabled'
        ).value

        if warning_enabled:
            if msg.data > threshold:
                self.get_logger().warn(
                    f'MOTOR HOT: {msg.data} C'
                )
            else:
                self.get_logger().info(
                    f'Motor normal: {msg.data} C'
                )
        else:
            self.get_logger().info(
                f'Temperature: {msg.data} C'
            )

    def reset_threshold_callback(self, request, response):

        self.set_parameters([
            Parameter(
                'warning_threshold',
                Parameter.Type.DOUBLE,
                45.0
            )
        ])

        response.success = True
        response.message = 'Warning threshold reset to 45.0 C'

        self.get_logger().info(response.message)

        return response


def main(args=None):
    rclpy.init(args=args)

    node = TemperatureSubscriber()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()
