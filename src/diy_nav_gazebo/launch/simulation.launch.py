#!/usr/bin/env python3
# ----------------------------------------------------------------------
# diy_nav_gazebo / launch/simulation.launch.py
# ----------------------------------------------------------------------
# 启动 Gazebo Classic 11 + diy_nav_bot 仿真（阶段 5）。
#
# 用法：
#   ros2 launch diy_nav_gazebo simulation.launch.py
#   ros2 launch diy_nav_gazebo simulation.launch.py world:=complex headless:=true
#
# 参数：
#   world        世界：empty | simple | complex 简写，或 .world 文件绝对路径
#                （默认 empty；simple/complex 在阶段 6 提供）
#   x / y / z    机器人出生位姿（默认 0 0 0.1；z 略高于地面让机器人落下稳定）
#   yaw          出生朝向（弧度，默认 0）
#   rviz         是否启动 RViz（默认 true）
#   headless     不启动 Gazebo GUI（默认 false，自动化测试请置 true）
#   use_sim_time 全部节点使用仿真时钟（默认 true）
#
# 同步机制：spawn_entity.py 自带 spawn service 等待（spawn_service_timeout），
#   无需在 launch 里硬编码延迟。shorthand → 路径映射与 gui 开关用
#   PythonExpression 做运行时求值（与 gzserver.launch.py 同款模式）。
# ----------------------------------------------------------------------
"""仿真 launch（阶段 5）."""

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (Command, LaunchConfiguration,
                                  PathJoinSubstitution, PythonExpression)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def _world_path(world_cfg):
    """把 empty/simple/complex 简写映射为包内世界文件路径，其余按原样透传."""
    share = get_package_share_directory('diy_nav_gazebo')
    return PythonExpression([
        "('", share, "/worlds/empty_world.world') if '", world_cfg, "' == 'empty'",
        " else ('", share, "/worlds/simple_world.world') if '", world_cfg, "' == 'simple'",
        " else ('", share, "/worlds/complex_world.world') if '", world_cfg, "' == 'complex'",
        " else '", world_cfg, "'",
    ])


def generate_launch_description():
    """生成仿真 launch 描述."""
    pkg_share = FindPackageShare('diy_nav_gazebo')

    return LaunchDescription([
        # ---------------- 参数 ----------------
        DeclareLaunchArgument('world', default_value='empty',
                              description='World: empty|simple|complex 或绝对路径'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.1'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        # Whether to shut down the whole launch when gzserver exits.
        DeclareLaunchArgument('server_required', default_value='false'),

        # ---------------- 机器人描述 ----------------
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'robot_description': ParameterValue(
                    Command(['xacro ',
                             PathJoinSubstitution(
                                 [FindPackageShare('diy_nav_description'),
                                  'urdf', 'diy_nav_bot.urdf.xacro'])]),
                    value_type=str),
            }],
        ),

        # ---------------- Gazebo server + client ----------------
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([FindPackageShare('gazebo_ros'),
                                      'launch', 'gazebo.launch.py'])),
            launch_arguments={
                'world': _world_path(LaunchConfiguration('world')),
                'gui': PythonExpression([
                    "'false' if '", LaunchConfiguration('headless'),
                    "' == 'true' else 'true'"]),
                'verbose': 'false',
                'server_required': LaunchConfiguration('server_required'),
            }.items(),
        ),

        # ---------------- 生成机器人 ----------------
        ExecuteProcess(
            cmd=['ros2', 'run', 'gazebo_ros', 'spawn_entity.py',
                 '-topic', 'robot_description',
                 '-entity', 'diy_nav_bot',
                 '-x', LaunchConfiguration('x'),
                 '-y', LaunchConfiguration('y'),
                 '-z', LaunchConfiguration('z'),
                 '-Y', LaunchConfiguration('yaw'),
                 '-spawn_service_timeout', '60',
                 '-timeout', '60'],
            output='screen',
        ),

        # ---------------- 激光过滤（车体自遮挡抑制） ----------------
        # Gazebo 传感器输出 /scan_raw → 过滤 <0.15 m 读数 → 重发 /scan
        Node(
            package='diy_nav_gazebo',
            executable='scan_filter.py',
            name='scan_filter',
            output='screen',
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        ),

        # ---------------- 可选 RViz ----------------
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', PathJoinSubstitution([pkg_share, 'rviz', 'simulation.rviz'])],
            condition=IfCondition(LaunchConfiguration('rviz')),
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
            output='screen',
        ),
    ])
