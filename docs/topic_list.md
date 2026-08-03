# Topic 清单（topic_list.md）

> 字段：名称 / 类型 / 发布节点 / 订阅节点 / 频率 / 作用 / 是否必须
> 状态：✅ 存在并验证（阶段 7 实测）；➖ 本阶段不存在（后续阶段加入）

| 名称 | 类型 | 发布节点 | 订阅节点 | 频率 | 作用 | 是否必须 |
|------|------|----------|----------|------|------|----------|
| `/clock` | rosgraph_msgs/msg/Clock | gzserver (`libgazebo_ros_init.so`) | 全部节点 | 1000 Hz | 仿真时钟，所有节点 `use_sim_time=true` | ✅ 必须 |
| `/cmd_vel` | geometry_msgs/msg/Twist | 遥控/导航节点（运行时） | `/diy_diff_drive` | 命令端决定 | 线速度/角速度指令 | ✅ 必须 |
| `/odom` | nav_msgs/msg/Odometry | `/diy_diff_drive` | 导航/里程订阅方 | 30 Hz | 里程计位姿（2D） | ✅ 必须 |
| `/tf` | tf2_msgs/msg/TFMessage | `/robot_state_publisher` + `/diy_diff_drive` | TF 消费者 | 30 Hz | 动态 TF（odom→base_footprint、关节 TF） | ✅ 必须 |
| `/tf_static` | tf2_msgs/msg/TFMessage | `/robot_state_publisher` | TF 消费者 | 一次性 + 变化 | 静态 TF（base_footprint→内部帧） | ✅ 必须 |
| `/joint_states` | sensor_msgs/msg/JointState | `/diy_joint_state` | `/robot_state_publisher` | 30 Hz | 左右轮关节角/角速度 | ✅ 必须 |
| `/scan` | sensor_msgs/msg/LaserScan | `/diy_laser_plugin` | SLAM/Nav2/RViz | 10 Hz | 720 点 360° 激光（0.12~8.0 m） | ✅ 必须 |
| `/imu` | sensor_msgs/msg/Imu | `/diy_imu_plugin` | SLAM/Nav2/RViz | 50 Hz | 三轴角速度/加速度/姿态 | ✅ 必须 |
| `/robot_description` | std_msgs/msg/String | `/robot_state_publisher` | spawn_entity、RViz | 一次性 | URDF 描述（供生成机器人） | ✅ 必须 |
| `/gazebo/model_states` | gazebo_msgs/msg/ModelStates | gzserver | 调试工具 | 1 Hz | 世界内全部模型位姿（调试用） | ➖ 调试 |
| `/spawn_entity` | gazebo_msgs/srv/SpawnEntity | gzserver | spawn_entity.py | 服务 | 生成实体（启动时一次性） | ➖ 启动用 |
| `/delete_entity` | gazebo_msgs/srv/DeleteEntity | gzserver | 用户 | 服务 | 删除实体（调试用） | ➖ 调试 |
| `/map` | nav_msgs/msg/OccupancyGrid | `/map_server`（阶段 8+） | AMCL/Nav2/RViz | 变化时 | 栅格地图 | ➖ 阶段 8+ |
| `/map_metadata` | nav_msgs/msg/MapMetaData | `/map_server`（阶段 8+） | `/map_server` | 变化时 | 地图元数据 | ➖ 阶段 8+ |
| `/initialpose` | geometry_msgs/msg/PoseWithCovarianceStamped | RViz/脚本 | `/amcl`（阶段 9+） | 命令 | AMCL 初始位姿 | ➖ 阶段 9+ |
| `/amcl_pose` | geometry_msgs/msg/PoseWithCovarianceStamped | `/amcl`（阶段 9+） | 导航消费者 | 10 Hz | AMCL 估计位姿 | ➖ 阶段 9+ |
| `/particlecloud` | geometry_msgs/msg/PoseArray | `/amcl`（阶段 9+） | RViz | 10 Hz | AMCL 粒子 | ➖ 阶段 9+ |
| `/navigate_to_pose/_action/…` | nav2_msgs/action/NavigateToPose | `/bt_navigator`（阶段 9+） | 导航客户端 | Action | 自主导航动作 | ➖ 阶段 9+ |
| `/global_costmap/…`、`/local_costmap/…` | nav2_msgs/msg/Costmap | costmap 节点（阶段 9+） | RViz/Nav2 | 10 Hz | 代价地图 | ➖ 阶段 9+ |
| `/plan` | nav_msgs/msg/Path | `/planner_server`（阶段 9+） | RViz | 变化时 | 全局路径 | ➖ 阶段 9+ |

## 必须性说明

- **✅ 必须**：本仿真方案正常工作的基础接口，缺一不可（`validate_simulation.sh` 逐项检查）；
- **➖ 调试/启动用**：Gazebo 自带服务与调试话题，不影响验收指标；
- **➖ 阶段 8+**：SLAM / 导航阶段的接口，届时在本表追加并标注实测频率。

## QoS 说明

- 传感器类（`/scan`、`/imu`、`/odom`、`/joint_states`、`/tf`）：Reliable + Volatile；
- `/clock`：Reliable + Volatile；
- 命令类（`/cmd_vel`）：Reliable；
- RViz 激光显示建议 Best Effort（与 Reliable 发布者兼容）。
