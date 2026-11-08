import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('a1_pubsub'), 'config', 'params.yaml')

    nodes = []
    for ns in ['robot1', 'robot2']:
        nodes.append(Node(
            package='a1_pubsub',
            executable='sine_publisher',
            namespace=ns,
            name='sine_publisher',
            parameters=[config],
        ))
        nodes.append(Node(
            package='a1_pubsub',
            executable='average_subscriber',
            namespace=ns,
            name='average_subscriber',
            parameters=[config],
        ))

    return LaunchDescription(nodes)