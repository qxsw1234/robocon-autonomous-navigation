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
"""SLAM Toolbox 建图 launch."""

import subprocess

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _check_no_cartographer(context):
    """互斥保护：若 Cartographer 正在运行则退出本 launch."""
    try:
        out = subprocess.run(
            ['ps', 'aux'], capture_output=True, text=True, timeout=15).stdout
    except Exception as e:
        raise RuntimeError(f'无法检查进程列表: {e}')
    for line in out.splitlines():
        if 'cartographer_node' in line:
            raise RuntimeError(
                '检测到 Cartographer 正在运行！不允许 SLAM Toolbox 与 '
                'Cartographer 同时运行（两者都会发布 map->odom）。\n'
                '请先停止 Cartographer 再启动 SLAM Toolbox。')
    return []


def generate_launch_description():
    """生成 SLAM Toolbox launch 描述."""
    pkg_share = FindPackageShare('diy_nav_navigation')

    return LaunchDescription([
        # 互斥保护（先于节点启动执行）
        OpaqueFunction(function=_check_no_cartographer),

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
