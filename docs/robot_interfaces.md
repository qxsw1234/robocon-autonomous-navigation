# 机器人接口说明（robot_interfaces.md）

本文档描述 `diy_nav_bot` 在 Gazebo Classic 11 仿真中的全部 ROS 2 接口：
**命令输入、状态输出、TF 发布**三部分。

## 1. 命令输入（机器人对外接口）

### `/cmd_vel`（geometry_msgs/msg/Twist）

- 发布节点：任何遥控/导航节点（如 `teleop_twist_keyboard`、Navigation2 的 `controller_server`）
- 订阅节点：`/diy_diff_drive`（Gazebo 差速驱动插件）
- 频率：命令端决定（Nav2 默认 ~20 Hz）
- 语义：`linear.x` 前进速度（m/s）、`angular.z` 转向角速度（rad/s，逆时针为正）
- 约束：插件未设速度上限（扭矩/加速度上限见 `config/gazebo_params.yaml`）；
  过大指令会造成打滑，导航时以 Nav2 参数中的 `max_vel_x` 等为准
- 默认 QoS：Reliable

## 2. 状态输出（感知与里程）

| Topic | 类型 | 发布节点 | 频率 | 说明 |
|-------|------|----------|------|------|
| `/odom` | nav_msgs/msg/Odometry | `/diy_diff_drive` | 30 Hz | 里程计位姿（2D，含协方差） |
| `/scan` | sensor_msgs/msg/LaserScan | `/diy_laser_plugin` | 10 Hz | 720 点 360° 激光，0.12~8.0 m，σ=0.01 |
| `/imu` | sensor_msgs/msg/Imu | `/diy_imu_plugin` | 50 Hz | 三轴角速度/加速度/姿态（底盘中心） |
| `/joint_states` | sensor_msgs/msg/JointState | `/diy_joint_state` | 30 Hz | 左右驱动轮关节角/角速度 |
| `/clock` | rosgraph_msgs/msg/Clock | gzserver | 1000 Hz | 仿真时钟（所有节点 use_sim_time） |

## 3. TF 发布（坐标系树）

| TF 对 | 发布节点 | 频率 | 说明 |
|-------|----------|------|------|
| `odom → base_footprint` | `/diy_diff_drive` | 30 Hz | 里程计位姿（全项目唯一来源） |
| `base_footprint → base_link → …` | `/robot_state_publisher` | 30 Hz | 机器人内部固定/关节 TF |
| 传感器 TF | `/robot_state_publisher` | 30 Hz | `laser_link`、`imu_link`、轮子 |

> ⚠️ `odom → base_footprint` 只允许 `/diy_diff_drive` 发布；SLAM（slam_toolbox /
> cartographer）与 AMCL 只发布 `map → odom`，绝无重复。

## 4. 传感器参数摘要（详情见 config/gazebo_params.yaml）

- **激光**：720 samples、−π~+π、10 Hz、量程 0.12~8.0 m、高斯噪声 σ=0.01 m、
  `frame_id=laser_link`（离地 0.23 m）
- **IMU**：50 Hz、`frame_id=imu_link`（底盘几何中心）、
  `initial_orientation_as_reference=false`（输出绝对姿态）
- **里程计**：差速模型，轮距 0.36 m、轮径 0.15 m，`odom→base_footprint` 由插件
  从机器人真实位姿投影发布（ENCODER 源）

## 5. 与服务/动作接口的关系

- 本阶段（仿真打通）仅涉及 Topic 与 TF；
- SLAM / Navigation2 阶段新增的服务与 Action 接口
  （`/map_server`、`/navigate_to_pose` 等）在 `docs/nav2_topics.md` 中说明。
