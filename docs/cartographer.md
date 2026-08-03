# Cartographer（cartographer.md）

## 概述

Cartographer（cartographer_ros 2.0.9）2D SLAM，基于局部子图 + 回环闭合
（scan-to-submap 匹配 + 稀疏位姿图）。本项目用作与 SLAM Toolbox 公平对比
的第二方案（阶段 12）。

## 关键配置（diy_nav_slam_compare/config/diy_nav_2d.lua，基线=官方 backpack_2d.lua）

| 项 | 值 | 说明 |
|----|----|------|
| map_frame | map | 地图系 |
| tracking_frame | base_footprint | 与 SLAM Toolbox / REP-103 一致 |
| published_frame | odom | 轨迹发布到 odom 系 |
| odom_frame | odom | 外部里程计 |
| provide_odom_frame | false | /odom 由差速驱动提供，不重复发布 |
| use_odometry | true | 订阅 /odom |
| use_imu_data | false | 与只使用激光+里程计的 SLAM Toolbox 公平比较 |
| min_range / max_range | 0.30 / 8.0 | 对齐 scan_filter 阈值与激光量程 |
| num_laser_scans | 1 | 单线激光（/scan_slam） |
| TRAJECTORY_BUILDER_2D.num_accumulated_range_data | 10 | 官方默认 |

## 工作流程

```text
/scan_slam + /odom + TF
  → 运动滤波器 → 子图（局部地图，scan-to-submap 匹配）
  → 全局回环闭合（稀疏位姿图优化）
  → 子图发布（0.3 s）→ occupancy_grid 节点合并为 /map
```

## 互斥保护

`cartographer.launch.py` 与 `slam_toolbox.launch.py` 双向 ps 进程级检测：
任一 SLAM 运行时启动另一个 → 拒绝并提示（两者都会发布 map→odom）。

## 建图实测（阶段 12-13）

- 在线同路线：50/50 航点（576 s），四门口占用 R1 0% / R2 0% / R3 1% /
  R4 0%——窄门口刻画显著优于 SLAM Toolbox（0% vs 8%）
- 离线回放同一 bag：门口 R1-R3 全 0%，R4 8%；走廊弥散噪声 903 格
  （SLAM Toolbox 59 格）——噪声更多但呈散点，不形成堵路块

## 启动

```bash
ros2 launch diy_nav_gazebo simulation.launch.py world:=complex rviz:=false
ros2 launch diy_nav_slam_compare cartographer.launch.py rviz:=true
```
