# diy_nav_slam_compare

`diy_nav_bot` 的 SLAM 对比工具包（SLAM Toolbox vs Cartographer）。

## 内容

| 目录 | 说明 |
|------|------|
| `diy_nav_slam_compare/` | Python 源码（`cli.py` 等） |
| `launch/` | 启动两种 SLAM 的对比 launch |
| `config/` | SLAM Toolbox / Cartographer 参数（YAML / Lua） |
| `scripts/` | 数据录制/回放、指标提取脚本 |
| `results/` | 建图结果输出目录（`raw/` 会被 .gitignore） |
| `resource/` | ament index 资源标记文件 |

## Console scripts

| 命令 | 入口 |
|------|------|
| `slam_compare_cli` | `diy_nav_slam_compare.cli:main` |

骨架阶段仅提供占位 CLI，后续阶段将新增比较节点。

## 状态

**骨架阶段（Phase 3）** — CLI 可运行但为占位实现。

## 构建

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select diy_nav_slam_compare
source install/setup.bash
ros2 run diy_nav_slam_compare slam_compare_cli
```

## Cartographer 2D SLAM（阶段 12）

与 SLAM Toolbox 公平对比的第二建图方案。

### 启动

```bash
# 终端 1：仿真（complex 世界）
ros2 launch diy_nav_gazebo simulation.launch.py world:=complex rviz:=false
# 终端 2：Cartographer（自动检测：slam_toolbox 运行中会拒绝启动）
ros2 launch diy_nav_slam_compare cartographer.launch.py rviz:=true
# 终端 3：同路线自动建图（50 航点，与 SLAM Toolbox 相同路线）
python3 ~/ros2_ws/src/diy_nav_navigation/scripts/mapping_tour.py
# 保存地图
python3 ~/ros2_ws/src/diy_nav_navigation/scripts/save_map.py \
  ~/ros2_ws/src/diy_nav_navigation/maps/complex_cartographer
```

### 主要配置（config/diy_nav_2d.lua，基线=官方 backpack_2d.lua）

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
| num_laser_scans | 1 | 单线激光（/scan_slam，RELIABLE 双发布） |

### 互斥保护

- cartographer.launch.py 与 slam_toolbox.launch.py 双向互检（ps 进程级检测）：
  任一 SLAM 运行时启动另一个 → 直接拒绝并提示。
- 原因：两个 SLAM 节点都会发布 `map -> odom`，同时运行会破坏 TF 单一来源。

### 验收记录（2026-08-03）

- 节点：cartographer_node + cartographer_occupancy_grid_node 正常
- /map：正常发布（320x176）
- 建图路线：50/50 航点完成（576 s，与 SLAM Toolbox 的 580 s 相近）
- 地图：门口占用 R1 0% / R2 0% / R3 1% / R4 0%（全通，优于 SLAM Toolbox 的 6-8%）；
  走廊噪声经同样清理流程处理后为 0（与 SLAM Toolbox 地图处理一致，保证对比公平）
