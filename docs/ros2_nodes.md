# ROS 2 节点清单（ros2_nodes.md）

## 仿真层（diy_nav_gazebo）

| 节点 | 包 | 作用 |
|------|----|------|
| gzserver | gazebo_ros | 物理仿真服务器（复杂世界） |
| gzclient | gazebo_ros | 仿真 GUI |
| spawn_entity.py | gazebo_ros | 从 robot_description 生成机器人 |
| robot_state_publisher | robot_state_publisher | 发布机器人 TF（关节 → link） |
| scan_filter | diy_nav_gazebo | /scan_raw → /scan（0.30 自遮挡抑制）+ /scan_slam 双发布 |

## SLAM 层

| 节点 | 包 | 作用 |
|------|----|------|
| slam_toolbox | slam_toolbox | 在线异步 2D SLAM（scan_slam + odom） |
| cartographer_node | cartographer_ros | 2D SLAM（同一数据，离线回放或在线） |
| cartographer_occupancy_grid_node | cartographer_ros | 子图 → 占用栅格 /map |

两 SLAM 互斥运行（launch 双向 ps 进程检测），避免双发 map→odom。

## 导航层（Nav2 1.1.20）

| 节点 | 包 | 作用 |
|------|----|------|
| map_server | nav2_map_server | 加载/发布静态地图 /map |
| amcl | nav2_amcl | 粒子滤波定位（发布 map→odom） |
| controller_server | nav2_controller | DWB 局部规划（FollowPath） |
| planner_server | nav2_planner | NavFn 全局规划（GridBased） |
| behavior_server | nav2_behaviors | 恢复行为（spin/backup/wait 等） |
| bt_navigator | nav2_bt_navigator | 行为树驱动整个导航流程 |
| waypoint_follower | nav2_waypoint_follower | 航点任务 |
| velocity_smoother | nav2_velocity_smoother | 速度平滑（限速/限加速度） |
| lifecycle_manager_* | nav2_lifecycle_manager | 生命周期管理（configure→activate） |

## 测试/工具层

| 脚本 | 作用 |
|------|------|
| mapping_tour.py | 50 航点自动建图路线（--no-map-check 用于录 bag） |
| nav_goal_runner.py | 5 目标自动导航测试（输出 CSV） |
| save_map.py | 从 /map 存 PGM+YAML（transient_local 直取） |
| validate_simulation.sh / teleop_test_suite.sh | 接口与运动验证 |
| smoke_test_bringup.sh | 一键启动冒烟测试 |

## 生命周期节点状态机

```text
unconfigured → configuring → inactive → activating → active
     ↑            |              |             |
     └────────────┴──────────────┴─────────────┘（deactivate/cleanup）
```
