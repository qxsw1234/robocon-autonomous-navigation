"""
display.launch.py - RViz visualization for diy_nav_bot.

Launches robot_state_publisher + joint_state_publisher (with optional GUI)
+ RViz2, using the packaged Xacro model. No Gazebo, no navigation.

Launch arguments
----------------
- use_sim_time (bool, default: false): if true, all nodes use /clock.
- use_gui      (bool, default: true) : if true, joint_state_publisher_gui
                                       provides sliders for the wheel joints;
                                       otherwise, the non-GUI joint publisher
                                       runs and keeps all joints at zero.
- rviz         (bool, default: true) : whether to start RViz2.
- model        (str)                 : full path to the Xacro model file.
                                       Defaults to the packaged file.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


PACKAGE_NAME = 'diy_nav_description'


def generate_launch_description() -> LaunchDescription:
    """Compose the launch description for the display pipeline."""
    pkg_share = get_package_share_directory(PACKAGE_NAME)
    default_model_path = os.path.join(pkg_share, 'urdf', 'diy_nav_bot.urdf.xacro')
    default_rviz_path = os.path.join(pkg_share, 'rviz', 'model.rviz')

    use_sim_time = LaunchConfiguration('use_sim_time')
    use_gui = LaunchConfiguration('use_gui')
    use_rviz = LaunchConfiguration('rviz')
    model = LaunchConfiguration('model')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true; false in this stage.',
    )
    declare_use_gui = DeclareLaunchArgument(
        'use_gui',
        default_value='true',
        description='Run joint_state_publisher_gui with sliders when true; '
                    'otherwise run the plain joint_state_publisher.',
    )
    declare_rviz = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Whether to start RViz2 with the packaged model.rviz.',
    )
    declare_model = DeclareLaunchArgument(
        'model',
        default_value=default_model_path,
        description='Full path to the robot Xacro file.',
    )

    # Expand Xacro at launch time; the ParameterValue wrapper marks the result
    # as a string so robot_state_publisher accepts it directly.
    robot_description = ParameterValue(
        Command(['xacro ', model]),
        value_type=str,
    )

    # robot_state_publisher publishes internal TF from the URDF.
    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_description,
        }],
    )

    # joint_state_publisher_gui: interactive sliders for continuous joints.
    jsp_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_gui),
    )

    # joint_state_publisher (non-GUI): keeps all continuous joints at zero.
    jsp_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        condition=UnlessCondition(use_gui),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', default_rviz_path],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_use_gui,
        declare_rviz,
        declare_model,
        rsp_node,
        jsp_gui_node,
        jsp_node,
        rviz_node,
    ])
