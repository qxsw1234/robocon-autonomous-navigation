#!/usr/bin/env python3
# ----------------------------------------------------------------------
# diy_nav_navigation / launch/bringup.launch.py
# ----------------------------------------------------------------------
# 一键启动（阶段 11）：仿真 + 机器人 + 感知 + SLAM 或导航。
#
#   ros2 launch diy_nav_navigation bringup.launch.py mode:=slam world:=complex rviz:=true
#   ros2 launch diy_nav_navigation bringup.launch.py mode:=navigation world:=complex rviz:=true
#
# 参数：
#   mode              slam | navigation（默认 slam）
#   world             empty | simple | complex（默认 complex）
#   map               导航模式地图 yaml（默认 complex_slam_toolbox.yaml）
#   slam_params_file  SLAM Toolbox 参数文件
#   nav2_params_file  Nav2 参数文件
#   rviz              是否启动 RViz（默认 true）
#   headless          无 GUI 运行 Gazebo（默认 false）
#   use_sim_time      使用仿真时钟（默认 true）
#   x y z yaw         机器人出生位姿
#   autostart         Nav2 生命周期自动激活（默认 true）
#
# 设计说明（执行约定）：
#   - 顺序：仿真（gzserver → 机器人 spawn → scan_filter）先起；SLAM/Nav2
#     节点自等待（scan/TF/map 就绪后开始工作），不依赖长 Timer。
#   - 清理：simulation.launch.py 透传 server_required=true → gzserver 退出
#     时整个 launch 关闭（不留残余节点）；Ctrl-C 同理。
#   - RViz：仿真自身 rviz 关闭，由本 launch 按模式透传给 SLAM/Nav2 各自
#     的 RViz 配置（slam.rviz / navigation.rviz）。
# ----------------------------------------------------------------------
"""一键启动 launch（阶段 11）."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (LaunchConfiguration, PathJoinSubstitution,
                                  PythonExpression)
from launch_ros.substitutions import FindPackageShare


def _include(pkg, launch_file, args, condition):
    # launch_arguments 必须传可迭代的 (key, value) 列表（dict 会被当作字符串迭代）
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(pkg), 'launch', launch_file])),
        launch_arguments=args.items(),
        condition=condition,
    )


def generate_launch_description():
    """生成 bringup launch 描述."""
    sim_args = {
        'world': LaunchConfiguration('world'),
        'x': LaunchConfiguration('x'),
        'y': LaunchConfiguration('y'),
        'z': LaunchConfiguration('z'),
        'yaw': LaunchConfiguration('yaw'),
        'headless': LaunchConfiguration('headless'),
        'use_sim_time': LaunchConfiguration('use_sim_time'),
        'rviz': 'false',  # RViz 由本 launch 按模式统一控制
        'server_required': 'true',  # gzserver 退出 → 整套关闭
    }
    is_slam = IfCondition(PythonExpression(
        ["'", LaunchConfiguration('mode'), "' == 'slam'"]))
    is_nav = IfCondition(PythonExpression(
        ["'", LaunchConfiguration('mode'), "' == 'navigation'"]))

    slam = _include(
        'diy_nav_navigation', 'slam_toolbox.launch.py',
        {
            'slam_params_file': LaunchConfiguration('slam_params_file'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'rviz': LaunchConfiguration('rviz'),
        },
        is_slam)

    loc = _include(
        'diy_nav_navigation', 'localization.launch.py',
        {
            'map': LaunchConfiguration('map'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': LaunchConfiguration('autostart'),
            'rviz': 'false',  # 定位 RViz 与导航 RViz 二选一，避免双开
            'nav2_params_file': LaunchConfiguration('nav2_params_file'),
        },
        is_nav)

    nav = _include(
        'diy_nav_navigation', 'navigation.launch.py',
        {
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': LaunchConfiguration('autostart'),
            'rviz': LaunchConfiguration('rviz'),
            'nav2_params_file': LaunchConfiguration('nav2_params_file'),
        },
        is_nav)

    return LaunchDescription([
        DeclareLaunchArgument('mode', default_value='slam',
                              description='slam | navigation'),
        DeclareLaunchArgument('world', default_value='complex',
                              description='empty | simple | complex'),
        DeclareLaunchArgument(
            'map',
            default_value=PathJoinSubstitution(
                [FindPackageShare('diy_nav_navigation'),
                 'maps', 'complex_slam_toolbox.yaml']),
            description='导航模式地图 yaml 路径'),
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=PathJoinSubstitution(
                [FindPackageShare('diy_nav_navigation'),
                 'config', 'slam_toolbox.yaml'])),
        DeclareLaunchArgument(
            'nav2_params_file',
            default_value=PathJoinSubstitution(
                [FindPackageShare('diy_nav_navigation'),
                 'config', 'nav2_params.yaml'])),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.1'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('autostart', default_value='true'),

        # 仿真（gzserver/gzclient/spawn/RSP/scan_filter）
        _include('diy_nav_gazebo', 'simulation.launch.py', sim_args,
                 IfCondition('true')),

        # SLAM 模式（只启 SLAM Toolbox）或导航模式（MapServer+AMCL+Nav2）
        slam,
        loc,
        nav,
    ])
