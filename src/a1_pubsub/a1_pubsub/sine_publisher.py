import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64


class SinePublisher(Node):
    def __init__(self):
        super().__init__('sine_publisher')

        self.amplitude = 1.0
        self.frequency = 0.5 

        if self.get_namespace() == '/robot2':
            self.frequency = 1.0

        self.rate_hz = 20.0

        self.publisher_ = self.create_publisher(Float64, 'signal', 10)
        self.timer = self.create_timer(1.0 / self.rate_hz, self.timer_callback)

        self.start_time = self.get_clock().now()

        self.get_logger().info(
            f'Publishing sine: A={self.amplitude}, f={self.frequency} Hz at {self.rate_hz} Hz'
        )

    def timer_callback(self):
        t = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        value = self.amplitude * math.sin(2.0 * math.pi * self.frequency * t)

        msg = Float64()
        msg.data = value
        self.publisher_.publish(msg)
        self.get_logger().info(f't={t:.2f}s  value={value:+.3f}')


def main(args=None):
    rclpy.init(args=args)
    node = SinePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()