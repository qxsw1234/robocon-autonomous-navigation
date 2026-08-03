#!/usr/bin/env python3
# ----------------------------------------------------------------------
# diy_nav_navigation / launch/slam_toolbox.launch.py
# ----------------------------------------------------------------------
# 启动 SLAM Toolbox（在线异步建图）。
# 注意：本 launch 不启动 Gazebo——请先启动仿真：
#   ros2 launch diy_nav_gazebo simulation.launch.py world:=complex
# 再启动建图：
#   ros2 launch diy_nav_navigation slam_toolbox.launch.py
#
# 参数：
#   slam_params_file  参数文件（默认包内 config/slam_toolbox.yaml）
#   use_sim_time      使用仿真时钟（默认 true）
#   rviz              是否启动 RViz（默认 true）
# ----------------------------------------------------------------------
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('diy_nav_navigation')

    return LaunchDescription([
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=PathJoinSubstitution(
                [pkg_share, 'config', 'slam_toolbox.yaml']),
            description='SLAM Toolbox 参数文件路径'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),

        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[
                LaunchConfiguration('slam_params_file'),
                {'use_sim_time': LaunchConfiguration('use_sim_time')},
            ],
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', PathJoinSubstitution([pkg_share, 'rviz', 'slam.rviz'])],
            condition=IfCondition(LaunchConfiguration('rviz')),
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
            output='screen',
        ),
    ])
