# 排障记录（troubleshooting.md）

> 只收录本项目实际出现并修复的错误，六段式格式。

## 1. 机器人急转后侧翻，车体灌入激光平面

- **现象**：急转擦墙后机器人侧翻（pitch 19.5°），地图中出现车体轮廓杂点，窄门口被"填死"。
- **错误日志**：无直接报错；gz 位姿显示 pitch/roll 异常；地图窄门口占用 29-43%。
- **根本原因**：轮线距质心仅 4.2 cm（wheel_x_offset −0.04），前翻角 15.7°，减速/冲击即前翻；万向轮承重仅 ~1.4%（临界稳定）。
- **排查过程**：对比 COM 与轮线位置 → 计算前翻角 → 观察 caster 承重（1.4N/109N）。
- **解决方法**：wheel_x_offset → −0.08（前翻角 28.7°，caster 承重 ~30%）；接触刚度 kp 1e6→1e8、kd 100→1；上盖收薄 0.08→0.02。
- **如何预防**：质心-轮线-万向轮三角稳定裕度检查纳入模型验收。

## 2. AMCL / costmap 收不到任何扫描（导航"失明"）

- **现象**：0/5 目标全败；AMCL 零粒子云、零 /amcl_pose；机器人直行撞墙；规划器 "failed to create plan"。
- **错误日志**：`AMCL cannot publish a pose or update the transform. Please set the initial pose...`；costmap 走廊被标 99 占用。
- **根本原因**：scan_filter 以 RELIABLE 发布 /scan，而 AMCL/costmap 的 ObservationBuffer 以 BEST_EFFORT 订阅——DDS QoS 不兼容，订阅端收不到任何消息（发布者更换后旧订阅甚至不重连）。
- **排查过程**：`ros2 topic info --verbose` 对比 QoS → rclpy BE 订阅验证（RELIABLE 端 0 帧）→ 重启 AMCL 无效 → 确认是发布端 QoS。
- **解决方法**：scan_filter 改 BE 发布 + 双发布 `/scan`(BE→Nav2) + `/scan_slam`(RELIABLE→SLAM)；全栈干净重启。
- **如何预防**：所有传感器话题用 rclpy 双 QoS 探测；topic info --verbose 核对兼容性。

## 3. 机器人空闲时缓慢旋转漂移（~2°/min）

- **现象**：静止 7 分钟偏航漂移 13°，每轮导航目标切换后 AMCL 信念-真实失配，机器人斜向贴墙。
- **错误日志**：无；gz 位姿与 odom 一致地缓慢旋转。
- **根本原因**：万向轮 mu=0 无偏航约束，ODE 接触抖动积分成持续旋转。
- **排查过程**：空闲 3 分钟对比位姿 → 排除 cmd_vel 残留 → 确认物理层漂移。
- **解决方法**：caster mu 0.0→0.05（3 分钟静止仅 0.007°，改善千倍；不阻碍原地旋转）。
- **如何预防**：空闲漂移测试纳入每次模型修改后的回归。

## 4. 地图走廊出现 0.4×0.4 m 机器人本体幽灵块

- **现象**：两处走廊（x≈±5.0）出现方形占用块，封死走廊导致规划失败。
- **错误日志**：无；地图 PGM 分析可见 32/25 格连通域。
- **根本原因**：车体角落距中心 0.276 m，0.23 m 过滤阈值只滤正面/侧面（0.225/0.16），角落读数穿透并被烘焙进地图（转点处）。
- **排查过程**：PGM 连通域分析 → 组件尺寸/位置比对世界几何 → 定位为转点烘焙。
- **解决方法**：过滤阈值 0.23→0.30（覆盖角落 0.276）；地图连通域清理脚本移除遗留块。
- **如何预防**：阈值必须 ≥ 车体最大外缘半径 + 裕量。

## 5. map_saver_cli 保存失败/落盘滞后

- **现象**：`Failed to spin map subscription`；或保存的 .pgm 与实时 /map 不一致（门口 29-43% vs 实时 6-13%）。
- **错误日志**：`[map_saver]: Failed to spin map subscription` → `Process exited with failure 1`。
- **根本原因**：本环境 DDS 发现/订阅偶发故障，CLI 工具一次性订阅不可靠。
- **排查过程**：rclpy transient_local 订阅对比 → 发现实时地图良好而落盘陈旧 → 定位为保存工具问题。
- **解决方法**：自研 `save_map.py`（transient_local 直取 latch，格式兼容 map_saver）。
- **如何预防**：地图保存统一走 save_map.py；保存前核对时间戳。

## 6. 窄门口（0.8 m）不可达/规划失败

- **现象**：R1 目标始终失败；规划器报 "GridBased: failed to create plan to (-2.20, 1.50)"。
- **错误日志**：`Planner algorithm GridBased failed to generate a valid path`。
- **根本原因**：inflation_radius 0.5 使门口两侧膨胀区重叠（0.8−2×0.5<0），代价地图中门口封死。
- **排查过程**：走廊代价梯度分析 → 门口通带计算 → 确认膨胀半径超标。
- **解决方法**：inflation_radius 0.5→0.2 + 过滤阈值 0.30（车体自身障碍团不再堵门）+ DWB 前瞻 1.7→1.0 s。
- **如何预防**：通带 = 门口宽 − 2×膨胀半径 ≥ 机器人宽度，纳入参数验收。

## 7. 生命周期节点激活卡死（unconfigured）

- **现象**：导航 6 节点停在 unconfigured/inactive，runner 永远等待。
- **错误日志**：`Timed out waiting for transform from base_footprint to map`（global_costmap）。
- **根本原因**：AMCL 未收到初始位姿 → 无 map→odom → costmap TF 不可用 → 生命周期激活失败。
- **排查过程**：GetState 逐节点检查 → 确认 AMCL 无初始位姿 → 发布后恢复。
- **解决方法**：启动后持续发布 /initialpose（25 s）+ 必要时手动 configure/activate；bringup 流程文档化。
- **如何预防**：启动顺序约定（先初始位姿后激活）；smoke_test 覆盖。

## 8. runner 初始位姿/目标被 AMCL/bt_navigator 拒绝

- **现象**：runner 发的初始位姿无效果（AMCL 日志无 initialPoseReceived）；目标不执行。
- **错误日志**：AMCL `Failed to transform initial pose in time (Lookup would require extrapolation into the future...)`。
- **根本原因**：消息时间戳用墙钟（rclpy.clock.Clock().now()），而 AMCL/bt 以仿真时钟工作。
- **解决方法**：节点开 use_sim_time，时间戳用节点时钟（nav.get_clock().now()）。
- **如何预防**：所有 use_sim_time 场景的消息一律用节点时钟打戳。

## 9. 双向互斥失效（DDS 节点残留）

- **现象**：slam_toolbox 已停止，Cartographer 启动仍被拒。
- **错误日志**：`检测到 slam_toolbox 正在运行...`（实际已停止）。
- **根本原因**：ros2 node list 依赖 DDS 发现，已停止节点残留在图里。
- **解决方法**：互斥检测改 ps 进程级。
- **如何预防**：进程级检测优先于图级检测。

## 10. 冒烟测试/录制脚本启动即失败

- **现象**：`AMENT_TRACE_SETUP_FILES: 未绑定的变量`。
- **错误日志**：`/opt/ros/humble/setup.bash: 行 8: AMENT_TRACE_SETUP_FILES: 未绑定的变量`。
- **根本原因**：脚本 `set -u` 在 source 之前，ament 脚本访问未定义变量。
- **解决方法**：先 source 再 set -u。
- **如何预防**：所有 source 的脚本遵循该顺序。
