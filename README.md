# diy_nav_bot — ROS 2 自主导航机器人项目

基于 **Ubuntu 22.04 + ROS 2 Humble + Gazebo Classic 11** 的自研差速机器人：
URDF 建模 → Gazebo 仿真 → 自定义世界 → SLAM（SLAM Toolbox / Cartographer 对比）→
AMCL 定位 → Navigation2 自主导航 → 一键启动。

> 环境说明：官方题目要求 Ubuntu 22.04 + ROS 2 Humble，本项目与该要求一致；
> Gazebo 采用与 Humble 兼容的 Classic 11。24.04 + Jazzy + Harmonic 仅是早期自设计划，并非官方要求。

## 考核完成情况

- **2.1 普通题**：DIY URDF/Xacro 机器人、自建 Gazebo 世界、SLAM Toolbox、AMCL、Navigation2 和自主导航闭环均已完成。
- **2.2 拓展题**：已部署 Cartographer，并使用同一个 rosbag 与 SLAM Toolbox 做 8 项指标和 30 次导航试验对比。
- **演示视频**：`results/videos/demo_navigation_rviz.mp4`，包含地图、机器人、全局路径、LaserScan、粒子云及实际自主导航过程；录制中第一个 7.5 m 走廊目标成功到达。
- **已知限制**：复杂长路线受 AMCL 走廊歧义影响，整体成功率约 13%～20%；失败数据和原因均如实保留。

## AI 工具使用说明

本项目在环境排查、代码调试、测试脚本设计、文档结构整理和录屏自动化过程中使用了 Codex、ZCode/Claude 等 AI 编程工具辅助。机器人模型、ROS 2 节点/Topic/TF、Nav2 参数、SLAM 对比方法和全部实验结论均由本人运行验证、理解后整理；AI 未替代实际仿真、建图或导航实验。详细过程见 `docs/development_record.md` 与 `docs/troubleshooting.md`。

## 安装

```bash
# 依赖（ROS 2 Humble 桌面版已装好前提下）：
sudo apt install ros-humble-gazebo-ros-pkgs ros-humble-slam-toolbox \
  ros-humble-nav2-bringup ros-humble-navigation2 ros-humble-cartographer-ros \
  ros-humble-tf2-tools ros-humble-nav2-simple-commander
```

## 构建

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## 运行空世界

```bash
ros2 launch diy_nav_gazebo simulation.launch.py world:=empty rviz:=true
```

## 运行简单世界

```bash
ros2 launch diy_nav_gazebo simulation.launch.py world:=simple rviz:=true
```

## 运行复杂世界

```bash
ros2 launch diy_nav_gazebo simulation.launch.py world:=complex rviz:=true
```

## 一键启动（阶段 11）

```bash
# SLAM 建图模式（自动起 Gazebo + 机器人 + SLAM Toolbox）
ros2 launch diy_nav_navigation bringup.launch.py mode:=slam world:=complex rviz:=true

# 导航模式（Map Server + AMCL + Nav2）
ros2 launch diy_nav_navigation bringup.launch.py mode:=navigation world:=complex rviz:=true
```

冒烟测试（SLAM/导航两模式 + 关闭清理验证）：

```bash
bash ~/ros2_ws/src/diy_nav_navigation/scripts/smoke_test_bringup.sh slam complex
bash ~/ros2_ws/src/diy_nav_navigation/scripts/smoke_test_bringup.sh navigation complex
```

## SLAM 建图

```bash
ros2 launch diy_nav_navigation bringup.launch.py mode:=slam world:=complex rviz:=true
# 另一终端：自动建图路线（50 航点，约 10 分钟）
python3 ~/ros2_ws/src/diy_nav_navigation/scripts/mapping_tour.py
```

## 保存地图

```bash
python3 ~/ros2_ws/src/diy_nav_navigation/scripts/save_map.py \
  ~/ros2_ws/src/diy_nav_navigation/maps/complex_slam_toolbox
```

（`save_map.py` 用 transient_local 直取 /map latch，格式与 map_saver 兼容；
`map_saver_cli` 在本环境偶发 "Failed to spin map subscription"，已弃用。）

## AMCL 定位

```bash
ros2 launch diy_nav_navigation localization.launch.py rviz:=true
# RViz 中用 “2D Pose Estimate” 或：
ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
  "{header: {frame_id: 'map'}, pose: {pose: {position: {x: 0.0, y: 0.0}, orientation: {w: 1.0}}}}"
```

## Nav2 导航

```bash
ros2 launch diy_nav_navigation navigation.launch.py rviz:=true
# 5 目标自动测试（走廊东端/R2 房间/R1 窄门口/R3 西南角/回起点）
python3 ~/ros2_ws/src/diy_nav_navigation/scripts/nav_goal_runner.py \
  --initial-x 0 --initial-y 0 --initial-yaw 0
```

## Cartographer 对比

```bash
# 终端 1：仿真
ros2 launch diy_nav_gazebo simulation.launch.py world:=complex rviz:=false
# 终端 2：Cartographer
ros2 launch diy_nav_slam_compare cartographer.launch.py rviz:=true
# 终端 3：同路线建图（复用 mapping_tour.py）
python3 ~/ros2_ws/src/diy_nav_navigation/scripts/mapping_tour.py
# 保存
python3 ~/ros2_ws/src/diy_nav_navigation/scripts/save_map.py \
  ~/ros2_ws/src/diy_nav_navigation/maps/complex_cartographer
```

## 常见错误

| 现象 | 原因 | 处理 |
|------|------|------|
| AMCL/代价地图无扫描数据 | scan_filter 曾以 RELIABLE 发布，AMCL/costmap 以 BEST_EFFORT 订阅，QoS 不兼容 | 已修复：/scan 用 BEST_EFFORT 双发布（/scan_slam 供 SLAM） |
| 机器人空闲时缓慢旋转漂移 | 万向轮 mu=0 无偏航约束 | 已修复：caster mu=0.05 |
| 地图走廊出现 0.4×0.4 幽灵块 | 车体角落读数 (0.276m) 穿透过滤阈值烘焙进地图 | 过滤阈值 0.30 + 连通域清理脚本 |
| 窄门口(0.8m)不可达 | inflation_radius 0.5 使两侧膨胀重叠封死门口 | 膨胀 0.2 + 过滤 0.30 |
| map_saver_cli 保存失败/滞后 | 该工具在本环境偶发 spin 超时 | 用 save_map.py |
| 生命周期节点激活卡住 | 无初始位姿时 AMCL 无 map→odom | 先在 RViz 设初始位姿 |

详细排障见 `src/diy_nav_navigation/docs/`。
