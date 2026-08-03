# ROS 2 话题清单（ros2_topics.md）

## 核心话题（七字段：话题/类型/方向/频率/发送者/接收者/说明）

| 话题 | 类型 | 方向 | 频率 | 发送者 | 接收者 | 说明 |
|------|------|------|------|--------|--------|------|
| /clock | rosgraph_msgs/Clock | pub | 10 Hz 节流 | gzserver | 全部 use_sim_time 节点 | 仿真时钟（BE） |
| /odom | nav_msgs/Odometry | pub | 30 Hz | 差速驱动 | AMCL/导航 | 里程计（真值） |
| /scan_raw | sensor_msgs/LaserScan | pub | 10 Hz | 激光插件 | scan_filter | 原始扫描（含自遮挡） |
| /scan | sensor_msgs/LaserScan | pub | 10 Hz | scan_filter | AMCL/costmap/RViz | 过滤后（<0.30 置 inf） |
| /scan_slam | sensor_msgs/LaserScan | pub | 10 Hz | scan_filter | SLAM Toolbox/Cartographer | RELIABLE 双发布 |
| /joint_states | sensor_msgs/JointState | pub | 30 Hz | 关节状态插件 | RSP | 轮关节角度 |
| /imu | sensor_msgs/Imu | pub | 50 Hz | IMU 插件 | （预留） | 本实验 SLAM 未用 IMU |
| /cmd_vel | geometry_msgs/Twist | sub | — | velocity_smoother | 差速驱动 | 速度指令（经平滑） |
| /tf | tf2_msgs/TFMessage | pub | 30 Hz | 差速驱动/RSP | 全部 | odom→base、关节 TF |
| /tf_static | tf2_msgs/TFMessage | pub | 静态 | RSP | 全部 | 固定 link TF |
| /map | nav_msgs/OccupancyGrid | pub | 2 s | SLAM 或 map_server | AMCL/costmap/RViz | 占用栅格（transient_local） |
| /initialpose | geometry_msgs/PoseWithCovarianceStamped | sub | — | RViz/脚本 | AMCL | 初始位姿（必须仿真时钟戳） |
| /amcl_pose | geometry_msgs/PoseWithCovarianceStamped | pub | 运动时 | AMCL | RViz | 定位估计 |
| /particle_cloud | geometry_msgs/PoseArray | pub | 运动时 | AMCL | RViz | 粒子云 |
| /plan | nav_msgs/Path | pub | 规划时 | planner_server | controller/RViz | 全局路径 |
| /local_plan | nav_msgs/Path | pub | 20 Hz | controller_server | RViz | 局部轨迹 |
| /global_costmap/costmap | nav_msgs/OccupancyGrid | pub | 1 Hz | planner_server | RViz | 全局代价地图 |
| /local_costmap/costmap | nav_msgs/OccupancyGrid | pub | 2 Hz | controller_server | RViz | 局部代价地图 |
| /goal_pose | geometry_msgs/PoseStamped | pub | 目标时 | BasicNavigator/RViz | RViz | 当前目标显示 |

## QoS 要点（本项目关键排障）

- Gazebo 传感器与 Nav2 的 ObservationBuffer 以 **BEST_EFFORT** 订阅；
  scan_filter 必须以 BE 发布 /scan（RELIABLE 会被 DDS 拒收）
- SLAM 栈以 RELIABLE 订阅 /scan_slam（BE 发布对其兼容性不保证 → 双发布）
- /map 使用 transient_local（latch），map_server 与 save_map.py 都依赖它
- /clock 为 BE；ros2 topic hz 在本环境不可靠，一律用 rclpy 探测
