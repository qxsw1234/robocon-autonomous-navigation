# TF 树说明（tf_tree.md）

## 1. 完整 TF 树

```
map                        （SLAM/AMCL 阶段加入，此处仅示意）
└── odom                   ← 由 Gazebo 差速驱动插件发布（世界原点=机器人出生位姿）
    └── base_footprint     ← 地面投影中心（z=0）
        └── base_link      ← 机器人主参考帧（离地 0.135 m，底盘几何中心）
            ├── chassis_link        (fixed, box 0.45×0.32×0.12)
            │   └── upper_body_link (fixed, 上盖)
            ├── left_wheel_link     (continuous, 轴沿 y)
            ├── right_wheel_link    (continuous, 轴沿 y)
            ├── front_caster_link   (fixed, 前万向轮)
            ├── laser_mount_link    (fixed, 雷达底座)
            │   └── laser_link      (fixed, 扫描平面，离地 0.23 m)
            └── imu_link            (fixed, IMU，底盘中心)
```

## 2. 各段 TF 的发布者（单一来源原则）

| TF 段 | 发布者 | 类型 | 频率 |
|-------|--------|------|------|
| `map → odom` | SLAM（slam_toolbox / cartographer）或 AMCL | 动态 | ~10 Hz |
| `odom → base_footprint` | `/diy_diff_drive`（Gazebo 插件） | 动态（里程计） | 30 Hz |
| `base_footprint → base_link → …` 全部内部 TF | `/robot_state_publisher` | 固定/关节 | 30 Hz |

**设计约束（项目开发约定）**：
1. `odom → base_footprint` 全项目唯一来源，禁止其他节点重复发布；
2. 禁止用静态 TF 冒充 SLAM/AMCL/里程计 TF；
3. 车轮 TF 由 RSP 从 `/joint_states` 发布（插件 `publish_wheel_tf=false`）。

## 3. 关键帧定义

| 帧 | 含义 | 位置 |
|----|------|------|
| `map` | 全局地图坐标系 | 由 SLAM/AMCL 定义（本阶段不存在） |
| `odom` | 里程计坐标系，原点=机器人出生位姿 | 世界固定 |
| `base_footprint` | 机器人地面 2D 投影中心 | 地面（z=0） |
| `base_link` | 机器人主参考帧 | 底盘几何中心（离地 0.135 m） |
| `laser_link` | 激光扫描平面原点 | base_link 上方 0.095 m（离地 0.23 m） |
| `imu_link` | IMU 原点 | 底盘几何中心（与 base_link 重合） |

## 4. 验证方法

```bash
# TF 连通性
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo base_footprint laser_link     # 期望 z=0.230
ros2 run tf2_ros tf2_echo base_footprint left_wheel_link  # 期望 y=0.18 z=0.075

# 重复 TF 检测（应恰好 2 个发布者：robot_state_publisher + diy_diff_drive）
ros2 topic info /tf -v | grep -B1 "Endpoint type: PUBLISHER" | grep "Node name:"
```
