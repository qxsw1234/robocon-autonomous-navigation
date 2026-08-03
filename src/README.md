# diy_nav_bot — ROS 2 自主移动机器人仿真项目

一个基于 **ROS 2 Humble** + **Gazebo Classic 11** 的自主移动机器人仿真工程，覆盖
URDF 建模、Gazebo 仿真、Navigation2 导航、以及 SLAM Toolbox / Cartographer 两种 SLAM 的对比评估。

## 一、项目目标

1. 使用 ROS 2 + Gazebo 搭建自主移动机器人仿真环境；
2. 自行编写机器人 URDF/Xacro；
3. 自行搭建 Gazebo 世界；
4. 部署 Navigation2；
5. 使用 SLAM Toolbox 完成基础建图；
6. 使用 Cartographer 完成第二种 SLAM；
7. 在相同环境和输入条件下比较两种 SLAM；
8. 完成导航演示、技术文档与录屏材料。

## 二、软件环境

| 项目 | 版本 |
|------|------|
| 操作系统 | Ubuntu 22.04.4 LTS |
| ROS 2 | Humble |
| Gazebo | Classic 11 |
| 桥接 | `gazebo_ros_pkgs` / `gazebo_ros` / `gazebo_plugins` |
| 导航 | Navigation2 (Humble) |
| SLAM | SLAM Toolbox + Cartographer |
| 工作空间 | `~/ros2_ws` |
| 机器人名称 | `diy_nav_bot` |

> ⚠️ 本项目为适配当前 Ubuntu 22.04 环境，使用 Gazebo Classic 11 + `gazebo_ros_pkgs`；
> 不使用 Gazebo Harmonic 或 `ros_gz`。

## 三、软件包说明

| 软件包 | 构建类型 | 职责 |
|--------|----------|------|
| `diy_nav_description` | `ament_cmake` | 机器人 URDF/Xacro、meshes、RViz 配置 |
| `diy_nav_gazebo` | `ament_cmake` | Gazebo 世界、模型、仿真 launch |
| `diy_nav_navigation` | `ament_cmake` | Nav2 参数、启动、地图、行为树 |
| `diy_nav_slam_compare` | `ament_python` | SLAM Toolbox vs Cartographer 对比工具 |

## 四、TF 树设计

```
map
└── odom
    └── base_footprint
        └── base_link
            ├── chassis_link
            │   └── upper_body_link
            ├── left_wheel_link
            ├── right_wheel_link
            ├── front_caster_link
            ├── laser_mount_link
            │   └── laser_link
            └── imu_link
```

TF 职责：

- `map -> odom` — SLAM Toolbox / Cartographer / AMCL
- `odom -> base_footprint` — Gazebo 差速驱动插件（全项目唯一来源）
- `base_footprint -> base_link` 及以下 — `robot_state_publisher`

## 五、构建方法

```bash
# 1. 打开新终端，确认 ROS 环境
source /opt/ros/humble/setup.bash
echo "$ROS_DISTRO"   # 应为 humble

# 2. 安装依赖（骨架阶段大部分依赖为运行时依赖，可跳过或部分失败）
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y || true

# 3. 构建
colcon build --symlink-install

# 4. Source
source install/setup.bash

# 5. 验证
ros2 pkg prefix diy_nav_description
ros2 pkg prefix diy_nav_gazebo
ros2 pkg prefix diy_nav_navigation
ros2 pkg prefix diy_nav_slam_compare
```

## 六、当前完成状态

| 阶段 | 状态 |
|------|------|
| 阶段 1：环境审计 | ✅ 完成（`~/ros2_project_environment_audit.md`） |
| 阶段 2：环境安装（Humble + Gazebo 11 + Nav2 + SLAM 全栈） | ✅ 完成 |
| 阶段 3：工作空间骨架（4 包） | ✅ 完成 |
| 阶段 4：URDF/Xacro 建模 + RViz 展示 | ✅ 完成 |
| 阶段 4.5：几何对齐规格（0.45×0.32 / 轮距 0.36 / 前 caster / 激光 0.23 m）+ 插件接口空壳 | ✅ 完成 |
| 阶段 5：Gazebo Classic 11 仿真接入（4 插件 + 空世界 + 运动验收 3/3） | ✅ **本阶段** |
| 阶段 6：自建世界（simple 10×8 / complex 16×12，纯 SDF 零 Fuel） | ✅ **本阶段** |
| 阶段 7：接口与 TF 验收 | ⏳ 未开始 |
| 阶段 8：SLAM Toolbox 建图 | ⏳ 未开始 |
| 阶段 9：AMCL + Navigation2 自主导航 | ⏳ 未开始 |
| 阶段 10：Nav2 参数调优 | ⏳ 未开始 |
| 阶段 11：一键 Bringup | ⏳ 未开始 |
| 阶段 12：Cartographer 建图 | ⏳ 未开始 |
| 阶段 13：公平对比实验 | ⏳ 未开始 |
| 阶段 14：最终交付（文档 + 检查清单） | ⏳ 未开始 |

## 七、目录结构

```
~/ros2_ws/
└── src/
    ├── diy_nav_description/
    ├── diy_nav_gazebo/
    ├── diy_nav_navigation/
    ├── diy_nav_slam_compare/
    └── README.md   ← 本文件
```

## 八、开发约定

- 所有节点统一 `use_sim_time: true`
- 参数集中在 YAML，不散落在 launch 文件
- Launch / YAML / Xacro 添加必要中文注释
- 禁止使用静态 TF 冒充 SLAM / AMCL / 里程计 TF
- 禁止多节点重复发布同一 TF
