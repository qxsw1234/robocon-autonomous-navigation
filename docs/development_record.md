# 自主导航项目开发记录

## 1. 任务与技术路线

本项目对应正式考核方向二：使用 ROS 2 Humble、Gazebo Classic 11 和 Navigation2，完成 DIY 差速机器人建模、自建仿真环境、SLAM 建图、AMCL 定位和自主导航；拓展部分部署 Cartographer，与 SLAM Toolbox 做公平比较。

开发按以下阶段推进：

1. 审计 Ubuntu/ROS/Gazebo 环境；
2. 编写 URDF/Xacro 和传感器接口；
3. 搭建 empty/simple/complex 三个世界；
4. 验证 `/clock`、`/odom`、`/scan`、`/imu`、`/joint_states` 与 TF；
5. 使用 SLAM Toolbox 建图并保存地图；
6. 部署 Map Server、AMCL、Navigation2；
7. 调整膨胀层、扫描过滤和 DWB 参数；
8. 部署 Cartographer，使用同一 rosbag 做离线公平比较；
9. 整理测试、报告、截图和演示视频。

## 2. 关键问题与改进

- 激光 QoS 不兼容导致 SLAM/AMCL 收不到扫描：拆分 `/scan` 与 `/scan_slam`，分别使用适合 Nav2 和 SLAM 的 QoS。
- 车体自遮挡形成地图幽灵块：加入近距离扫描过滤并调整阈值。
- 0.8 m 窄门口被代价地图膨胀封死：将膨胀半径从 0.5 m 调整到 0.2 m。
- AMCL 在长直走廊存在定位多解：保留 3 轮 × 5 目标的真实失败数据，并把它作为系统限制分析，而非删除失败案例。
- 两种 SLAM 对比容易受输入路线影响：固定同一 rosbag、同一参数和同一导航目标，记录 CPU、内存、地图质量与导航指标。

完整错误现象、原因、修复和验证过程见 `troubleshooting.md`，Nav2 参数变化见 `src/diy_nav_navigation/docs/nav2_tuning_log.md`。

## 3. 最终结果

- `colcon test`：34 tests，0 errors，0 failures，1 skipped；
- SLAM Toolbox 与 Cartographer 均完成 50/50 航点建图；
- SLAM 对比包含 8 项指标和 30 次导航试验；
- 演示录屏中 7.5 m 走廊目标自主导航成功；
- 长路线总体成功率约 13%～20%，已如实记录。

## 4. AI 工具使用说明

开发过程中使用 Codex、ZCode/Claude 等 AI 编程工具辅助环境排查、代码调试、测试脚本设计、资料整理和录屏自动化。所有 ROS 2 节点、Topic、TF、Nav2 参数、SLAM 对比实验和结论均由本人在本机实际运行、检查日志并理解后整理。AI 未替代实际建图、导航或数据采集。
