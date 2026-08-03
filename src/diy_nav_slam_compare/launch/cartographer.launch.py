#!/usr/bin/env python3
# ----------------------------------------------------------------------
# diy_nav_slam_compare / launch/cartographer.launch.py
# ----------------------------------------------------------------------
# 启动 Cartographer 2D SLAM（阶段 12，与 SLAM Toolbox 对比方案）。
#
#   ros2 launch diy_nav_slam_compare cartographer.launch.py rviz:=true
#
# 前置：仿真已启动（simulation.launch.py world:=complex）。
# 互斥保护：检测到 slam_toolbox 正在运行则直接退出（不允许两个 SLAM
# 节点同时运行 / 同时发布 map->odom）。
#
# 参数：
#   configuration_directory   Lua 配置目录（默认包内 config/）
#   configuration_basename    Lua 文件名（默认 diy_nav_2d.lua）
#   scan_topic                激光话题（默认 /scan_slam，RELIABLE 双发布）
#   use_sim_time              使用仿真时钟（默认 true）
#   rviz                      是否启动 RViz（默认 true）
# ----------------------------------------------------------------------
import os
import subprocess

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _check_no_slam_toolbox(context):
    """互斥保护：若 slam_toolbox 正在运行则退出本 launch。
    用 ps 进程级检测（DDS 发现延迟会让已停止节点残留在图里）。"""
    try:
        out = subprocess.run(
            ['ps', 'aux'], capture_output=True, text=True, timeout=15).stdout
    except Exception as e:
        raise RuntimeError(f'无法检查进程列表: {e}')
    for line in out.splitlines():
        if 'async_slam_toolbox_node' in line:
            raise RuntimeError(
                '检测到 slam_toolbox 正在运行！不允许 Cartographer 与 '
                'SLAM Toolbox 同时运行（两者都会发布 map->odom）。\n'
                '请先停止 SLAM Toolbox 再启动 Cartographer。')
    return []


def generate_launch_description():
    pkg_share = FindPackageShare('diy_nav_slam_compare')
    default_config_dir = PathJoinSubstitution([pkg_share, 'config'])
    default_rviz = PathJoinSubstitution([pkg_share, 'rviz', 'cartographer.rviz'])

    return LaunchDescription([
        # 互斥保护（先于节点启动执行）
        OpaqueFunction(function=_check_no_slam_toolbox),

        DeclareLaunchArgument(
            'configuration_directory', default_value=default_config_dir,
            description='Cartographer Lua 配置目录'),
        DeclareLaunchArgument(
            'configuration_basename', default_value='diy_nav_2d.lua'),
        DeclareLaunchArgument('scan_topic', default_value='/scan_slam'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),

        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
            arguments=['-configuration_directory',
                       LaunchConfiguration('configuration_directory'),
                       '-configuration_basename',
                       LaunchConfiguration('configuration_basename')],
            remappings=[('scan', LaunchConfiguration('scan_topic')),
                        ('odom', '/odom')],
        ),

        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            output='screen',
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', default_rviz],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
