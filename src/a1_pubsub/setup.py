from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'a1_pubsub'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='saket',
    maintainer_email='saket.nadimpalla@gmail.com',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'talker = a1_pubsub.talker:main',
            'listener = a1_pubsub.listener:main',
            'sine_publisher = a1_pubsub.sine_publisher:main',
            'average_subscriber = a1_pubsub.average_subscriber:main',
        ],
    },
)
