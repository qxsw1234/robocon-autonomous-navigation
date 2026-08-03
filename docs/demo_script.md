# 演示视频脚本（demo_script.md）

> 目标时长 8-12 分钟。每节：预计时长 / 屏幕 / 台词要点 / 命令 / 易出问题。

## 1. 项目介绍（30 s）
- **屏幕**：项目标题 + 机器人 CAD 渲染（RViz 模型特写）
- **台词**：自研差速移动机器人，完成 ROS 2 下从建模、仿真、建图到自主导航的完整闭环，并做两种 SLAM 的公平对比。
- **命令**：无

## 2. 软件环境（30 s）
- **屏幕**：`ros2 --version`、`dpkg -l | grep gazebo`、`ros2 pkg list | grep -E "slam_toolbox|cartographer"`
- **台词**：Ubuntu 22.04 + ROS 2 Humble + Gazebo Classic 11 + Nav2 1.1.20 + SLAM Toolbox 2.6.10 + Cartographer 2.0.9。计划原面向 24.04+Jazzy+Harmonic，本环境如实采用 Humble 生态。
- **命令**：`ros2 --version`

## 3. 工程目录（30 s）
- **屏幕**：`tree ~/ros2_ws/src -L 2`
- **台词**：四个包：description（模型）、gazebo（仿真）、navigation（SLAM/导航）、slam_compare（对比实验）。
- **命令**：`tree`

## 4. URDF/Xacro 讲解（60 s）
- **屏幕**：`cat properties.xacro` + `xacro diy_nav_bot.urdf.xacro | check_urdf`
- **台词**：参数化尺寸单一来源；稳定裕度设计（轮线后移 8.2 cm、前翻角 28.7°）；TF 单一来源约定。
- **命令**：`check_urdf`
- **易出问题**：xacro 展开后 XML 注释不能含 `--`。

## 5. RViz 机器人模型（40 s）
- **屏幕**：RViz RobotModel + TF 显示
- **台词**：base_footprint→base_link→轮/激光/IMU 完整树。
- **命令**：`ros2 launch diy_nav_description display.launch.py`

## 6. Gazebo DIY 环境（60 s）
- **屏幕**：gzclient 的 complex 世界
- **台词**：16×12 m，四房间+走廊+0.8 m 窄门口+U/L 障碍+遮挡区；纯 SDF 基本几何体，零 Fuel 依赖。
- **命令**：`ros2 launch diy_nav_gazebo simulation.launch.py world:=complex`

## 7. 遥控与传感器（60 s）
- **屏幕**：teleop_twist_keyboard + `ros2 topic echo /scan --once` + RViz 激光
- **台词**：/odom 30 Hz、/scan 10 Hz（过滤后）、/imu 50 Hz。
- **命令**：`ros2 run teleop_twist_keyboard teleop_twist_keyboard`

## 8. TF 树（40 s）
- **屏幕**：`ros2 run tf2_ros view_frames`
- **台词**：map→odom（SLAM/AMCL）→base_footprint（差速驱动）→各 link（RSP）；无重复发布。
- **命令**：`view_frames`

## 9. SLAM Toolbox 建图（90 s）
- **屏幕**：RViz 地图增长 + Gazebo 机器人巡航
- **台词**：50 航点自动路线，580 s；四门口全通。
- **命令**：`ros2 launch diy_nav_navigation bringup.launch.py mode:=slam` + `python3 mapping_tour.py`
- **易出问题**：需等 /map 出现后再巡航；扫描 QoS 需 /scan_slam。

## 10. 保存并加载地图（40 s）
- **屏幕**：`save_map.py` 输出 + 预览图
- **台词**：transient_local 直取，避免 map_saver_cli 偶发失败。
- **命令**：`python3 save_map.py maps/complex_slam_toolbox`
- **易出问题**：保存前确认 /map 时间戳为最新。

## 11. AMCL 定位（60 s）
- **屏幕**：RViz 粒子云 + 2D Pose Estimate
- **台词**：粒子滤波；先设初始位姿再激活导航节点（否则生命周期卡死）。
- **命令**：`ros2 launch diy_nav_navigation localization.launch.py`
- **易出问题**：初始位姿必须用仿真时钟戳。

## 12. Nav2 多点导航（90 s）
- **屏幕**：RViz 5 目标序列（走廊东端→R2→R1 窄门口→R3→回起点）
- **台词**：Nav2 六大节点协作；走廊直行与窄门口专项通过；长路线受 AMCL 走廊歧义限制（如实说明成功率）。
- **命令**：`ros2 launch diy_nav_navigation navigation.launch.py` + `nav_goal_runner.py`

## 13. Cartographer 建图（60 s）
- **屏幕**：cartographer RViz（子图 + 轨迹）
- **台词**：同路线 50/50；与 SLAM Toolbox 互斥保护。
- **命令**：`ros2 launch diy_nav_slam_compare cartographer.launch.py`

## 14. 两种 SLAM 对比（60 s）
- **屏幕**：两地图并排 + 对比报告表格
- **台词**：同一 rosbag 离线回放保证公平；8 项指标；SLAM Toolbox 省资源、Cartographer 门口更准。
- **命令**：`generate_report.py`

## 15. 总结（30 s）
- **屏幕**：结论页
- **台词**：完整闭环 + 公平对比 + 已知局限如实记录。
- **命令**：无

## 总时长 ≈ 11 分钟
