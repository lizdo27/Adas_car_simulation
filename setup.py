import os
from setuptools import find_packages, setup

package_name = 'gazebo_sim_adas'

# 1. Khai báo các file bắt buộc của gói ROS 2
data_files = [
    ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
]

# 2. Quét tự động thư mục world_model và media để đưa vào hệ thống
for folder in ['world_model', 'media']:
    for path, _, filenames in os.walk(folder):
        if filenames:
            file_paths = [os.path.join(path, f) for f in filenames]
            data_files.append((os.path.join('share', package_name, path), file_paths))

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=data_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='lizdo',
    maintainer_email='lizdo@todo.todo',
    description='Hệ thống ADAS tích hợp YOLOv8 và bộ điều khiển PID',
    license='TODO: License declaration',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'lane_detector_node=gazebo_sim_adas.lane_detector:main',
            'video_recorder_node=gazebo_sim_adas.record_video:main',
            'ute_lane_assist=gazebo_sim_adas.lane_assist:main',
        ],
    },
)