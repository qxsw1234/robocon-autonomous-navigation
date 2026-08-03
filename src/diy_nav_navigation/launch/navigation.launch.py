#!/usr/bin/env python3
# ----------------------------------------------------------------------
# diy_nav_navigation / launch/navigation.launch.py
# ----------------------------------------------------------------------
# 启动 Navigation2 导航栈（planner/controller/behaviors/bt/waypoint/smoother）。
# 前置：仿真 + 定位（localization.launch.py）已启动。
#   ros2 launch diy_nav_navigation navigation.launch.py
#
# 参数：
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

NAVIGATION_NODES = [
    'controller_server',
    'planner_server',
    'behavior_server',
    'bt_navigator',
    'waypoint_follower',
    'velocity_smoother',
]


def generate_launch_description():
    pkg_share = FindPackageShare('diy_nav_navigation')
    default_params = PathJoinSubstitution(
        [pkg_share, 'config', 'nav2_params.yaml'])

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('autostart', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('nav2_params_file', default_value=default_params),

        Node(package='nav2_controller', executable='controller_server',
             name='controller_server', output='screen',
             parameters=[LaunchConfiguration('nav2_params_file'),
                         {'use_sim_time': LaunchConfiguration('use_sim_time')}]),
        Node(package='nav2_planner', executable='planner_server',
             name='planner_server', output='screen',
             parameters=[LaunchConfiguration('nav2_params_file'),
                         {'use_sim_time': LaunchConfiguration('use_sim_time')}]),
        Node(package='nav2_behaviors', executable='behavior_server',
             name='behavior_server', output='screen',
             parameters=[LaunchConfiguration('nav2_params_file'),
                         {'use_sim_time': LaunchConfiguration('use_sim_time')}]),
        Node(package='nav2_bt_navigator', executable='bt_navigator',
             name='bt_navigator', output='screen',
             parameters=[LaunchConfiguration('nav2_params_file'),
                         {'use_sim_time': LaunchConfiguration('use_sim_time')}]),
        Node(package='nav2_waypoint_follower', executable='waypoint_follower',
             name='waypoint_follower', output='screen',
             parameters=[LaunchConfiguration('nav2_params_file'),
                         {'use_sim_time': LaunchConfiguration('use_sim_time')}]),
        Node(package='nav2_velocity_smoother', executable='velocity_smoother',
             name='velocity_smoother', output='screen',
             parameters=[LaunchConfiguration('nav2_params_file'),
                         {'use_sim_time': LaunchConfiguration('use_sim_time')}]),

        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'autostart': LaunchConfiguration('autostart'),
                'node_names': NAVIGATION_NODES,
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
