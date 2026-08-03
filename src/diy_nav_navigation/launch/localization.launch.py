#!/usr/bin/env python3
# ----------------------------------------------------------------------
# diy_nav_navigation / launch/localization.launch.py
# ----------------------------------------------------------------------
# 启动 AMCL 定位（map_server + amcl + lifecycle manager）。
# 前置：仿真已启动 + 地图已存在（阶段 8 产物）。
#   ros2 launch diy_nav_gazebo simulation.launch.py world:=complex headless:=true
#   ros2 launch diy_nav_navigation localization.launch.py
#
# 参数：
#   map               地图 yaml 路径（默认包内 maps/complex_slam_toolbox.yaml）
#   use_sim_time      使用仿真时钟（默认 true）
#   autostart         lifecycle 自动激活（默认 true）
#   rviz              是否启动 RViz（默认 true）
#   nav2_params_file  Nav2 参数文件（默认包内 config/nav2_params.yaml）
# ----------------------------------------------------------------------
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('diy_nav_navigation')

    default_map = PathJoinSubstitution(
        [pkg_share, 'maps', 'complex_slam_toolbox.yaml'])
    default_params = PathJoinSubstitution(
        [pkg_share, 'config', 'nav2_params.yaml'])

    return LaunchDescription([
        DeclareLaunchArgument('map', default_value=default_map,
                              description='地图 yaml 文件路径'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('autostart', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('nav2_params_file', default_value=default_params),

        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[
                LaunchConfiguration('nav2_params_file'),
                {'yaml_filename': LaunchConfiguration('map')},
                {'use_sim_time': LaunchConfiguration('use_sim_time')},
            ],
        ),

        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[
                LaunchConfiguration('nav2_params_file'),
                {'use_sim_time': LaunchConfiguration('use_sim_time')},
            ],
        ),

        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'autostart': LaunchConfiguration('autostart'),
                'node_names': ['map_server', 'amcl'],
            }],
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', PathJoinSubstitution([pkg_share, 'rviz', 'navigation.rviz'])],
            condition=IfCondition(LaunchConfiguration('rviz')),
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
            output='screen',
        ),
    ])
