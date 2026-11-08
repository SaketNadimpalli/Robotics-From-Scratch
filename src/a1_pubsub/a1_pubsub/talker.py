import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_msgs.msg import Float64


class Talker(Node):

    def __init__(self):
        super().__init__('my_talker')
        self.publisher_ = self.create_publisher(Float64, 'chatter', 10)
        self.timer = self.create_timer(0.5, self.timer_callback)
        self.count = 0

    def timer_callback(self):
        msg = Float64()
        msg.data = float(self.count)
        #msg.data = f'Hello from my node: {self.count}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.count = self.count + 1

def main(args=None):
    rclpy.init(args=args)
    node = Talker()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
