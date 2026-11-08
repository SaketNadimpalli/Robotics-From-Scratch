import rclpy
from rclpy.node import Node
from a3_interfaces.srv import GetStats


class StatsClient(Node):
    def __init__(self):
        super().__init__('stats_client')
        self.declare_parameter('last_n', 20)
        self.stats_client = self.create_client(GetStats, 'get_stats')

    def request_stats(self):
        if not self.stats_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('get_stats service not available')
            return None

        request = GetStats.Request()
        request.last_n = self.get_parameter('last_n').value

        future = self.stats_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        return future.result()


def main(args=None):
    rclpy.init(args=args)
    node = StatsClient()

    response = node.request_stats()
    if response is not None:
        node.get_logger().info(
            f'count={response.count}  mean={response.mean:+.3f}  '
            f'min={response.min:+.3f}  max={response.max:+.3f}'
        )

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()