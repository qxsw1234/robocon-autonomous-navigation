# diy_nav_description

`diy_nav_bot`（DIY 差速移动机器人）的 **URDF/Xacro 描述**、meshes 与 RViz 配置。

## 一、软件包用途

提供 diy_nav_bot 的静态描述（几何、坐标、材质、惯性）与 RViz 可视化 launch。
**不含**：Gazebo 世界、传感器插件、里程计、SLAM 或导航配置——这些属于后续阶段。

## 二、机器人设计目标

一个用于室内 SLAM 与自主导航实验的两轮差速移动机器人：

- 低矮矩形底盘 + 上盖（更好看，允许后期加装其他部件）
- 左右各一个驱动轮，后方一个球形万向支撑轮
- 顶部安装 2D 激光雷达（架于圆柱底座上，便于扫描）
- 底盘中心安装 IMU 外观盒（后续阶段接入 IMU 传感器插件）

## 三、机器人尺寸

| 部件 | 长/半径 | 宽/长度 | 高/宽度 | 质量 |
|------|---------|---------|---------|------|
| 底盘 chassis | 0.46 m | 0.34 m | 0.12 m | 8.0 kg |
| 上盖 upper_body | 0.38 m | 0.28 m | 0.08 m | 1.5 kg |
| 驱动轮（cyl，轴沿 y） | r=0.075 m | l=0.035 m | — | 0.60 kg（×2） |
| 后万向轮（球） | r=0.035 m | — | — | 0.15 kg |
| 激光底座 | r=0.045 m | l=0.035 m | — | 0.20 kg |
| 激光 laser_link | r=0.030 m | l=0.010 m | — | 0.03 kg |
| IMU 盒 | 0.05 m | 0.04 m | 0.02 m | 0.05 kg |

- 左右轮心距离 `wheel_separation`：0.31 m
- 万向轮相对底盘中心的 x 偏移：−0.16 m
- 激光扫描平面高度（laser_link 中心离地）：≈ 0.265 m

**机器人总质量 ≈ 11.13 kg**（8.0 + 1.5 + 2·0.60 + 0.15 + 0.20 + 0.03 + 0.05）。

## 四、文件结构

```
diy_nav_description/
├── CMakeLists.txt
├── LICENSE
├── package.xml
├── README.md                     ← 本文件
├── launch/
│   └── display.launch.py         ← 加载 rsp + jsp[_gui] + RViz
├── urdf/
│   ├── diy_nav_bot.urdf.xacro    ← 主文件，仅 include 各模块
│   ├── properties.xacro          ← 所有尺寸/质量/位置常量
│   ├── materials.xacro           ← 视觉颜色（RGBA）
│   ├── inertial_macros.xacro     ← box/cylinder/sphere 惯性宏
│   ├── base.xacro                ← base_footprint / base_link / chassis / upper_body
│   ├── wheels.xacro              ← 左右轮 + 后万向轮
│   └── sensors.xacro             ← 激光雷达底座 + 激光帧 + IMU
├── meshes/                       ← 预留 mesh 资源（当前空）
├── rviz/
│   └── model.rviz                ← Grid + RobotModel + TF + Axes
└── scripts/
    └── validate_description.sh   ← 静态验证（xacro/urdf/结构/禁止内容）
```

## 五、Xacro 模块说明

- **properties.xacro** — 集中定义所有尺寸和位置常量。修改机器人参数时**只改这里**。
- **materials.xacro** — 6 种颜色（`diy_blue/dark/gray/black/red/lidar`），不使用外部纹理。
- **inertial_macros.xacro** — `box_inertial`、`cylinder_inertial`、`sphere_inertial` 三个惯性宏，接受 `<origin>` 块，支持旋转的惯性坐标系。
- **base.xacro** — `base_footprint`（无几何）+ `base_link`（参考帧）+ `chassis_link`（box 主体）+ `upper_body_link`（顶部盒）。
- **wheels.xacro** — 定义 `diy_wheel` 宏，左右轮按 y 轴对称摆放；圆柱轴通过 `rpy="pi/2 0 0"` 旋转让轴沿 y。后万向轮为球体近似 + fixed joint。
- **sensors.xacro** — 激光雷达（`laser_mount_link → laser_link`）+ `imu_link`。**本阶段没有 `<gazebo>` 标签，没有传感器插件。**

## 六、Link 说明

| Link | 几何 | 说明 |
|------|------|------|
| `base_footprint` | 无 | 地面 2D 参考坐标（z=0） |
| `base_link` | 无 | 机器人主参考帧（抬升 0.135 m） |
| `chassis_link` | box | 主底盘 |
| `upper_body_link` | box | 底盘上盖 |
| `left_wheel_link` | cylinder | 左驱动轮 |
| `right_wheel_link` | cylinder | 右驱动轮 |
| `rear_caster_link` | sphere | 后万向轮（球体近似） |
| `laser_mount_link` | cylinder | 激光雷达底座 |
| `laser_link` | cylinder | 激光扫描参考帧 |
| `imu_link` | box | IMU 外观盒（底盘中心） |

## 七、Joint 说明

| Joint | 类型 | Parent → Child |
|-------|------|----------------|
| `base_footprint_to_base_link` | fixed | base_footprint → base_link |
| `base_link_to_chassis` | fixed | base_link → chassis_link |
| `chassis_to_upper_body` | fixed | chassis_link → upper_body_link |
| `left_wheel_joint` | **continuous** | base_link → left_wheel_link（axis 0 1 0） |
| `right_wheel_joint` | **continuous** | base_link → right_wheel_link（axis 0 1 0） |
| `rear_caster_joint` | fixed | base_link → rear_caster_link |
| `laser_mount_joint` | fixed | base_link → laser_mount_link |
| `laser_joint` | fixed | laser_mount_link → laser_link |
| `imu_joint` | fixed | base_link → imu_link |

## 八、TF 树

```
base_footprint
└── base_link (fixed)
    ├── chassis_link (fixed)
    │   └── upper_body_link (fixed)
    ├── left_wheel_link  (continuous, axis y)
    ├── right_wheel_link (continuous, axis y)
    ├── rear_caster_link (fixed)
    ├── laser_mount_link (fixed)
    │   └── laser_link (fixed)
    └── imu_link (fixed)
```

## 九、`base_footprint` 与 `base_link` 的区别

- `base_footprint`：机器人**在地面上的二维投影中心**，z 恒为 0。SLAM / 里程计后续会
  发布 `odom → base_footprint`。
- `base_link`：机器人**主参考帧**，位于底盘几何中心（离地 0.135 m）。所有内部部件挂到此。

`base_footprint → base_link` 是 **fixed** 关系，`robot_state_publisher` 发布。

## 十、惯性公式

- 盒体：`Ixx = m(y²+z²)/12`, `Iyy = m(x²+z²)/12`, `Izz = m(x²+y²)/12`
- 圆柱（轴沿 z）：`Ixx=Iyy = m(3r²+h²)/12`, `Izz = mr²/2`；轮子调用时 origin `rpy="π/2 0 0"` 使轴对齐 y
- 球体：`Ixx=Iyy=Izz = 2mr²/5`
- 所有具有物理实体的 Link 都有正定惯性；`base_footprint` 和 `base_link` 是纯参考帧，不含惯性

## 十一、如何构建

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select diy_nav_description
source install/setup.bash
```

## 十二、如何静态检查

```bash
# xacro 展开
xacro "$(ros2 pkg prefix diy_nav_description)/share/diy_nav_description/urdf/diy_nav_bot.urdf.xacro" > /tmp/diy_nav_bot.urdf

# URDF 结构检查
check_urdf /tmp/diy_nav_bot.urdf
```

## 十三、如何启动 RViz

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

# 交互式（joint_state_publisher_gui 拖动滑块转动左右轮）
ros2 launch diy_nav_description display.launch.py

# 无 GUI（自动化测试）
ros2 launch diy_nav_description display.launch.py use_gui:=false rviz:=false
```

Launch 参数：
- `use_sim_time`（默认 `false`）— 本阶段无仿真时钟
- `use_gui`（默认 `true`）— 使用 GUI 版 joint_state_publisher
- `rviz`（默认 `true`）— 启动 RViz2
- `model`（默认已安装的 Xacro 路径）— 加载其它 Xacro 时使用

## 十四、如何运行验证脚本

```bash
bash ~/ros2_ws/src/diy_nav_description/scripts/validate_description.sh
```

或从 install 空间：
```bash
ros2 run diy_nav_description validate_description.sh
```

脚本会依次输出 `[PASS]/[WARN]/[FAIL]`，最后总结。若任意 FAIL 存在，退出码非零。

## 十五、当前阶段限制（阶段 4）

**当前阶段仅完成 URDF/RViz 展示**，尚未实现：

- Gazebo 物理仿真（无 `<gazebo>` 标签）
- 差速驱动插件 / 里程计 / `/odom`
- 2D 激光雷达数据 / `/scan`
- IMU 数据 / `/imu`
- SLAM（SLAM Toolbox 或 Cartographer）
- 自主导航（Navigation2）
- `map` 或 `odom` 坐标帧
- 静态 TF 冒充上述帧

后万向轮当前使用**球体外观 + fixed joint** 作为简化模型，后续 Gazebo 物理仿真
阶段会根据接触和摩擦测试重新评估是否需要真实自由度。

## 十六、下一阶段计划（阶段 5）

- 编写 Gazebo Classic 11 世界（自建 `ground_plane` 与 `sun`）
- 加入 `<gazebo>` 标签：`libgazebo_ros_diff_drive.so`（发布 `odom → base_footprint` 与 `/odom`）
- 激光雷达 `libgazebo_ros_ray_sensor.so`（发布 `/scan`）
- IMU `libgazebo_ros_imu_sensor.so`（发布 `/imu`）
- 组合 `diy_nav_bringup.launch.py` 启动仿真
