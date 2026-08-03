# 项目总览（project_overview.md）

## 一句话

基于 **ROS 2 Humble + Gazebo Classic 11** 的自研差速移动机器人（diy_nav_bot），
完成从 URDF 建模、仿真验证、SLAM 建图（SLAM Toolbox / Cartographer 双方案）、
AMCL 定位到 Navigation2 自主导航的完整闭环，并提供可复现的公平 SLAM 对比实验。

## 环境（如实记录与计划的偏差）

| 项 | 计划 | 实际环境 | 影响 |
|----|------|---------|------|
| 系统 | Ubuntu 24.04 | Ubuntu 22.04.4 | 所有包按 Humble 实装 |
| ROS 2 | Jazzy | **Humble** | 无 Jazzy 对应包，全部用 Humble 官方源 |
| Gazebo | Harmonic | **Gazebo Classic 11.10.2** | 世界文件用 SDF 1.x 基本几何体，零 Fuel 依赖 |
| Nav2 | Jazzy 版 | **1.1.20** | 参数/节点名按 Humble 实装核对 |
| SLAM Toolbox | — | **2.6.10** | 官方 online_async 基线 |
| Cartographer | — | **2.0.9** | 官方 backpack_2d.lua 基线 |

偏差已全程如实记录，未伪造任何 Jazzy/Harmonic 特性。

## 项目结构

```text
ros2_ws/
├── src/
│   ├── diy_nav_description/    URDF/Xacro 机器人模型（4.5 阶段）
│   ├── diy_nav_gazebo/         Gazebo 世界、仿真 launch、扫描过滤（5-7 阶段）
│   ├── diy_nav_navigation/     SLAM/定位/导航 launch、地图、测试脚本（8-11 阶段）
│   └── diy_nav_slam_compare/   Cartographer + 公平对比实验（12-13 阶段）
├── docs/                       15 份交付文档（14 阶段）
└── README.md                   安装/构建/运行指南
```

## 成果概览

- 机器人：0.45×0.32 m 差速底盘，0.075 m 轮径，前万向轮，2D 激光 720 线/10 Hz，
  稳定裕度 28.7°（前翻角），caster 微摩擦消除空闲漂移
- 世界：empty/simple/complex 三个自建 SDF 世界（complex 16×12 m，四房间+走廊+
  0.8 m 窄门口+U/L 障碍+遮挡区）
- 建图：SLAM Toolbox 与 Cartographer 同路线 50/50 航点完成，四门口全通
- 导航：Nav2（AMCL+DWB）5 目标自动测试；走廊直行与窄门口专项通过
- 对比：同一 rosbag 离线回放 + 8 项指标 + 30 次导航试验（见 slam_comparison.md）
- 一键启动：`bringup.launch.py mode:=slam|navigation`，冒烟测试全 PASS

## 已知限制（诚实记录）

- Nav2 长路线成功率受 AMCL 走廊歧义限制（~13-20%，详见 nav2_tuning_log.md）
- 导航成功率非 SLAM 算法差异所致，两地图在同参数下对比
