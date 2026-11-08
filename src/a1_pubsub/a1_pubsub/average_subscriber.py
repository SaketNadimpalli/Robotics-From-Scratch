from collections import deque

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64


class AverageSubscriber(Node):
    def __init__(self):
        super().__init__('average_subscriber')

        self.window = deque(maxlen=20) 

        self.publisher_ = self.create_publisher(Float64, 'signal_avg', 10)
        self.subscription = self.create_subscription(
            Float64, 'signal', self.listener_callback, 10
        )

    def listener_callback(self, msg):
        self.window.append(msg.data)

        avg = sum(self.window) / len(self.window)

        out = Float64()
        out.data = avg
        self.publisher_.publish(out)
        self.get_logger().info(
            f'raw={msg.data:+.3f}  avg={avg:+.3f}  (n={len(self.window)})'
        )


def main(args=None):
    rclpy.init(args=args)
    node = AverageSubscriber()
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