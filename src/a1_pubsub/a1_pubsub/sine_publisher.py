import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from rcl_interfaces.msg import SetParametersResult

import time

from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from a3_interfaces.action import RampAmplitude


class SinePublisher(Node):
    def __init__(self):
        super().__init__('sine_publisher')

        self.declare_parameter('amplitude', 1.0)
        self.declare_parameter('frequency', 0.5)
        self.declare_parameter('rate_hz', 20.0)

        self.amplitude = self.get_parameter('amplitude').value
        self.frequency = self.get_parameter('frequency').value
        self.rate_hz = self.get_parameter('rate_hz').value

        self.publisher_ = self.create_publisher(Float64, 'signal', 10)
        self.timer = self.create_timer(1.0 / self.rate_hz, self.timer_callback)

        self.start_time = self.get_clock().now()

        self.add_on_set_parameters_callback(self.on_params)

        self.get_logger().info(
            f'Publishing sine: A={self.amplitude}, f={self.frequency} Hz at {self.rate_hz} Hz'
        )

        self.action_server = ActionServer(
            self,
            RampAmplitude,
            'ramp_amplitude',
            execute_callback=self.execute_ramp,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=ReentrantCallbackGroup(),
        )

    def on_params(self, params):
        for p in params:
            if p.name == 'frequency':
                if p.value <= 0.0:
                    return SetParametersResult(successful=False, reason='frequency must be > 0')
                self.frequency = p.value
        return SetParametersResult(successful=True)

    def timer_callback(self):
        t = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        value = self.amplitude * math.sin(2.0 * math.pi * self.frequency * t)

        msg = Float64()
        msg.data = value
        self.publisher_.publish(msg)
        self.get_logger().info(f't={t:.2f}s  value={value:+.3f}')

    def goal_callback(self, goal_request):
        if goal_request.duration <= 0.0:
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        return CancelResponse.ACCEPT

    def execute_ramp(self, goal_handle):
        start = self.amplitude
        target = goal_handle.request.target_amplitude
        steps = max(1, int(goal_handle.request.duration * 20))

        feedback = RampAmplitude.Feedback()
        result = RampAmplitude.Result()

        for i in range(1, steps + 1):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                result.final_amplitude = self.amplitude
                result.completed = False
                return result

            fraction = i / steps
            self.amplitude = start + (target - start) * fraction

            feedback.current_amplitude = self.amplitude
            feedback.progress = fraction
            goal_handle.publish_feedback(feedback)

            time.sleep(0.05)

        goal_handle.succeed()
        result.final_amplitude = self.amplitude
        result.completed = True
        return result


def main(args=None):
    rclpy.init(args=args)
    node = SinePublisher()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()