# ROS 2 Humble 学习笔记

> 学习环境：Ubuntu 22.04、ROS 2 Humble、Gazebo Classic 11  
> 实践项目：`diy_nav_bot` 自主导航仿真  
> 记录目的：说明本次考核中对 ROS 2 基础通信、TF、仿真时间和 Nav2 数据流的理解，而不是只记录运行命令。

## 1. 从工作空间开始

ROS 2 工作空间通常包含四个目录：

| 目录 | 作用 | 是否应提交到 GitHub |
|---|---|---|
| `src/` | 源码、launch、配置、URDF/Xacro | 是 |
| `build/` | CMake、Python 包等构建中间文件 | 否 |
| `install/` | 构建后的可执行文件、环境脚本 | 否 |
| `log/` | `colcon` 构建和测试日志 | 通常不提交 |

本项目使用的基本流程：

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
colcon test
colcon test-result --verbose
```

`source /opt/ros/humble/setup.bash` 用于加载系统安装的 ROS 2；`source install/setup.bash` 用于让终端发现当前工作空间中新构建的包。新开终端后如果忘记第二步，会出现“package not found”或找不到新修改节点的情况。

`--symlink-install` 对 Python、launch 和配置文件调试比较方便，但修改 C++、接口定义或安装规则后仍需要重新构建。

## 2. 包、节点与命名

- **包（package）**：ROS 2 工程的组织与分发单位。本项目拆分为机器人描述、Gazebo 仿真、导航和 SLAM 对比四个包。
- **节点（node）**：实际运行的进程或组件。例如 `robot_state_publisher`、`amcl`、`controller_server`。
- **Topic、Service、Action、Parameter**：节点之间的通信和配置接口。

我常用以下命令确认系统是否按预期启动：

```bash
ros2 pkg list
ros2 node list
ros2 node info /amcl
ros2 topic list -t
ros2 service list -t
ros2 action list -t
ros2 param list /controller_server
```

学习体会：launch 文件成功启动并不等于系统可用。还需要检查节点是否存在、生命周期节点是否 active、Topic 是否有数据、TF 是否连通。

## 3. Topic 发布与订阅

Topic 适合连续数据流，发布者和订阅者通过“话题名 + 消息类型”连接，双方不需要互相知道具体节点名。

本项目的典型 Topic：

| Topic | 消息类型 | 发布者 | 主要订阅者/用途 |
|---|---|---|---|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Nav2 或遥控节点 | 差速驱动插件，控制线速度和角速度 |
| `/odom` | `nav_msgs/msg/Odometry` | Gazebo 差速驱动 | Nav2、定位和调试节点 |
| `/scan` | `sensor_msgs/msg/LaserScan` | 激光插件/过滤节点 | AMCL、Nav2 代价地图 |
| `/imu` | `sensor_msgs/msg/Imu` | IMU 插件 | 状态与传感器验证 |
| `/map` | `nav_msgs/msg/OccupancyGrid` | SLAM 或 map_server | RViz、AMCL、Nav2 |
| `/tf`、`/tf_static` | `tf2_msgs/msg/TFMessage` | 多个 TF 发布者 | 所有需要坐标变换的节点 |
| `/clock` | `rosgraph_msgs/msg/Clock` | Gazebo | 使用仿真时间的全部节点 |

常用检查方法：

```bash
ros2 topic info /scan --verbose
ros2 topic echo /scan --once
ros2 topic hz /scan
ros2 topic bw /scan
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.0}}"
```

### QoS 的实际问题

ROS 2 Topic 不仅要名称和类型一致，QoS 也必须兼容。传感器数据常使用 `BEST_EFFORT`，可靠控制或状态信息常使用 `RELIABLE`。本项目曾出现 SLAM/AMCL 收不到激光数据的问题：Topic 名存在、`echo` 也能看到数据，但发布端和订阅端 QoS 不匹配。

解决方法是先用 `ros2 topic info /scan --verbose` 查看发布/订阅端 QoS，再根据用途拆分 `/scan` 与 `/scan_slam`，分别适配 Nav2 和 SLAM。由此理解到：“有 Topic”不等于“订阅成功”，排障必须同时检查类型、QoS、频率和时间戳。

## 4. Service、Action 与 Parameter

### Service

Service 是一次请求、一次响应，适合短时间完成的操作，例如查询状态、触发保存或切换功能。调用方会等待结果，因此不适合持续数据和长时间运动任务。

```bash
ros2 service list -t
ros2 service type /example_service
```

### Action

Action 适合耗时任务，包含目标、过程反馈和最终结果，也支持取消。Nav2 的 `NavigateToPose` 使用 Action，因为机器人到达目标需要较长时间，执行过程中还需要反馈剩余距离和状态。

```bash
ros2 action list -t
ros2 action info /navigate_to_pose
```

### Parameter

Parameter 用于配置节点行为，例如 AMCL 粒子数量、DWB 速度限制、代价地图分辨率和膨胀半径。参数通常写在 YAML 中，由 launch 文件加载。

本项目中把膨胀半径从 0.5 m 调整为 0.2 m 后，0.8 m 窄门不再被代价地图完全封闭。这说明参数不是孤立数值，必须结合机器人外形、地图分辨率和环境尺寸调试。

```bash
ros2 param get /local_costmap/local_costmap inflation_layer.inflation_radius
ros2 param dump /controller_server
```

## 5. TF2 坐标变换

自主导航的核心 TF 链为：

```text
map -> odom -> base_footprint -> base_link -> laser_link / imu_link / wheel_link
```

- `map -> odom`：由 SLAM 或 AMCL 提供，用于修正里程计长期漂移。
- `odom -> base_footprint`：由差速驱动提供，要求连续、平滑，但允许长期累计误差。
- `base_footprint -> base_link -> sensors`：由 URDF 和 `robot_state_publisher` 提供，表示机器人内部固定或关节坐标关系。

常用检查：

```bash
ros2 run tf2_ros tf2_echo map base_footprint
ros2 run tf2_tools view_frames
```

本项目坚持每条 TF 只由一个节点负责。例如 `odom -> base_footprint` 只由差速驱动发布，避免两个发布者相互覆盖造成机器人在 RViz 中跳动。排查 TF 问题时，我按“父子坐标系是否存在—时间戳是否有效—发布频率是否正常—是否重复发布”的顺序检查。

## 6. 仿真时间与时间戳

Gazebo 通过 `/clock` 发布仿真时间。仿真中的 ROS 2 节点需要设置：

```yaml
use_sim_time: true
```

如果某个节点使用系统时间、其他节点使用仿真时间，会出现 TF extrapolation、消息时间戳过旧、导航节点等待数据等问题。因此启动后应确认 `/clock` 有数据，并检查 AMCL、Nav2、RViz 等节点的 `use_sim_time`。

这也解释了为什么设置初始位姿时需要使用仿真时钟：时间基准不一致时，即使位姿数值正确，TF 也可能拒绝变换。

## 7. rosbag 与可重复实验

`rosbag2` 可以记录 Topic 数据，用于离线回放、复现问题和公平对比：

```bash
ros2 bag record /scan /scan_slam /odom /tf /tf_static /clock
ros2 bag info <bag目录>
ros2 bag play <bag目录> --clock
```

本项目使用同一段约 582 s 的 rosbag 分别运行 SLAM Toolbox 和 Cartographer，尽量保证输入轨迹、传感器数据和时间一致。与“分别遥控两次”相比，这样能减少路线差异对算法比较的影响。

## 8. 从 ROS 2 基础到 Nav2 的数据流

我的理解不是把 Nav2 看成一个单独程序，而是多个节点通过 Topic、TF、Action 和 Parameter 协作：

1. Gazebo 发布 `/scan`、`/odom`、`/imu`、`/clock`；
2. `robot_state_publisher` 和驱动插件组成机器人 TF；
3. SLAM 建图，或者 map_server 加载已有地图；
4. AMCL 根据地图、激光和里程计估计机器人在 `map` 中的位置；
5. Planner 根据目标生成全局路径；
6. Controller 根据路径和局部代价地图输出 `/cmd_vel`；
7. Behavior Server 在受阻时执行恢复动作；
8. Lifecycle Manager 统一配置和激活 Nav2 节点。

导航失败时不能只看最终“失败”提示。我会依次检查：传感器 Topic、TF、定位粒子、全局/局部代价地图、全局路径、局部控制输出和恢复行为。

## 9. 本次学习中的实际问题与收获

| 问题 | 原因 | 处理与收获 |
|---|---|---|
| 激光存在但 SLAM 无数据 | QoS 不兼容 | 学会检查 QoS，并按用途拆分话题 |
| 地图出现机器人附近幽灵障碍 | 激光照到自身或近距离噪声 | 增加近距离扫描过滤 |
| 窄门在代价地图中被封闭 | 膨胀半径相对门宽过大 | 参数应结合机器人尺寸调节 |
| AMCL 在长走廊定位歧义 | 环境特征重复、观测退化 | 保留失败数据，不把规划问题和定位问题混淆 |
| 节点已启动但导航不可用 | 生命周期节点未激活或时间不一致 | 同时检查 lifecycle、`/clock` 和 TF |

最大的收获是形成了分层排障思路：先验证单个 Topic 和 TF，再检查定位与地图，最后检查规划控制。ROS 2 系统中的故障往往不是某个节点完全崩溃，而是接口、QoS、时间或坐标系之间存在不一致。

## 10. 相关项目记录

- 节点与职责：[`ros2_nodes.md`](ros2_nodes.md)
- Topic 与 QoS：[`ros2_topics.md`](ros2_topics.md)
- TF 树：[`tf_tree.md`](tf_tree.md)
- Nav2 流程：[`nav2_workflow.md`](nav2_workflow.md)
- Nav2 参数：[`nav2_parameters.md`](nav2_parameters.md)
- 实际排障：[`troubleshooting.md`](troubleshooting.md)
- 完整开发过程：[`development_record.md`](development_record.md)

本笔记记录的是本次考核中已经实际使用和验证的部分。后续还需要继续学习 ROS 2 组件化节点、DDS 实现差异、实时性、跨机器网络通信和真实机器人上的传感器同步。
