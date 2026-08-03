# 答辩问题准备（defense_questions.md）

> 全部答案基于本项目实测与真实环境，如实回答（含环境偏差）。

## 环境与选型

**Q1. 为什么使用 ROS 2 Humble 而不是计划中的 Jazzy？**
A：本机环境为 Ubuntu 22.04，Humble 是其官方 ROS 2 发行版；Jazzy 对应 24.04。
计划原面向 Jazzy+Harmonic，执行中如实改用 Humble 生态（Nav2 1.1.20、
Gazebo Classic 11），所有差异已在文档记录，未伪造任何 Jazzy 特性。

**Q2. Gazebo Classic 与 Harmonic 有什么区别？**
A：Classic 是 ROS 1 时代的经典仿真器（gzserver/gzclient，SDF 1.x），
Humble 官方支持；Harmonic 是新一代（gz sim，SDF 2.x，新传输层）。
本环境无 Harmonic 对应依赖，故用 Classic 11，世界文件用 SDF 基本几何体。

**Q3. URDF 和 SDF 有什么区别？**
A：URDF 描述单机器人（link/joint/惯性/碰撞），Gazebo 插件需扩展标签；
SDF 描述整个世界（含场景、光照、物理），也可含模型。本项目机器人用
URDF/Xacro（含 gazebo_ros 插件），世界用 SDF。

**Q4. base_link 和 base_footprint 有什么区别？**
A：base_footprint 是机器人在地面的投影（z=0），是导航/定位的基准；
base_link 是底盘本体坐标系（本项目 z=0.135）。中间用固定关节连接，
由 robot_state_publisher 发布。

**Q5. map、odom、base_link 分别表示什么？**
A：map 是全局地图系（固定，世界原点）；odom 是里程计系（随起点，漂移
但连续）；base_link 是机器人系。定位通过 map→odom 将两者桥接。

**Q6. map→odom 是谁发布的？**
A：建图时由 SLAM（SLAM Toolbox 或 Cartographer）发布；导航时由 AMCL 发布。
两者互斥运行（launch 双向进程检测），避免同时发布。

**Q7. odom→base_footprint 是谁发布的？**
A：差速驱动插件（gazebo_ros_diff_drive），以轮编码器模型积分，30 Hz。
本项目 TF 单一来源原则：该变换全项目唯一来源。

**Q8. 为什么不能重复发布 TF？**
A：TF 树要求每对父子帧只有一个权威来源；重复发布会造成变换跳变、
缓冲混乱（lookup 歧义），AMCL/代价地图的 TF 查询会失败或给出错误结果。

## 数据与消息

**Q9. /scan 是什么类型？**
A：sensor_msgs/msg/LaserScan：angle_min/max/increment、range_min/max、
ranges[]（720 线、10 Hz、0.12~8.0 m）。本项目经 scan_filter 过滤后
<0.30 m 置 inf。

**Q10. /odom 包含什么？**
A：nav_msgs/Odometry：位姿（位置+四元数）、速度（线/角）、协方差；
header 帧 base_footprint、child_frame odom。仿真中为真值。

**Q11. /cmd_vel 是什么？**
A：geometry_msgs/Twist（线速度+角速度），Nav2 经 velocity_smoother
限速后发布给差速驱动执行。

**Q12. Topic、Service、Action 有什么区别？**
A：Topic 是异步发布/订阅（连续数据流）；Service 是同步请求/响应（一次性
调用）；Action 是长时任务（目标/反馈/结果三阶段，可取消）。

**Q13. 为什么导航使用 Action？**
A：导航是长时任务（几十秒到几分钟），需要中途反馈（进度/恢复次数）、
可取消、可区分成功/失败，Action 恰好提供这三段式接口。

## SLAM 与定位

**Q14. SLAM Toolbox 如何工作？**
A：扫描匹配（相关性+ Ceres 精配）→ 位姿图插入（运动阈值 0.5 m/0.5 rad）
→ 回环搜索（扫描缓冲 + 响应阈值）→ 图优化 → 周期发布 /map（2 s）。

**Q15. Cartographer 如何工作？**
A：scan-to-submap 匹配建局部子图（submap），全局稀疏位姿图回环闭合，
occupancy_grid 节点把子图合并为 /map。

**Q16. 两种 SLAM 有什么区别？**
A：实测（同一 bag）：SLAM Toolbox 计算开销低（CPU 均值 3.1% vs 6.5%、
峰值 19% vs 74%）、走廊噪声少（59 vs 903）；Cartographer 窄门口精度高
（占用 0% vs 8%）、地图范围大但未知区 9.1%。

**Q17. AMCL 是什么？**
A：自适应蒙特卡洛定位（粒子滤波）：以里程计预测 + 激光似然校正，估计
机器人在地图中的位姿，发布 map→odom。

**Q18. 为什么建图后还需要 AMCL？**
A：建图得到的 map→odom 是建图过程的历史轨迹；新会话中机器人位置未知，
需要 AMCL 用当前扫描重新定位（初始位姿 + 粒子收敛）。

**Q19. AMCL 的走廊歧义是什么？**
A：长直走廊扫描沿纵向平移不变，粒子在 x 方向权重接近 → 重采样随机性
使信念沿走廊漂移（本实验长路线 map→odom 可走 3 m）。缓解：运动噪声
趋零（alpha 0.01）+ 匹配锐化（likelihood 0.3）。这是本项目导航成功率
（13-20%）的主要限制，非 SLAM 算法差异。

## Nav2

**Q20. Nav2 有哪些主要节点？**
A：map_server、amcl、planner_server、controller_server、behavior_server、
bt_navigator、waypoint_follower、velocity_smoother + 两个 lifecycle manager。

**Q21. planner_server 做什么？**
A：全局规划：在全局代价地图（静态地图+障碍+膨胀）上用 NavFn 搜索到
目标的路径，发布 /plan。

**Q22. controller_server 做什么？**
A：局部规划：DWB 在局部代价地图（滚动窗口 3×3 m）上采样轨迹（前向×角向），
评分选最优，输出 /cmd_vel。

**Q23. bt_navigator 做什么？**
A：行为树驱动：规划→跟踪→进度检查→（失败）恢复行为→重试，直至成功/失败。

**Q24. global costmap 和 local costmap 有什么区别？**
A：全局：整张地图、map 系、1 Hz、含静态层；局部：机器人周围滚动窗口、
odom 系、5 Hz、无静态层（靠实时扫描）。

**Q25. inflation radius 有什么作用？**
A：把障碍物向外膨胀出代价梯度，使规划路径与障碍保持距离。本项目从 0.5
收缩到 0.2：0.8 m 窄门口的通带 = 0.8−2×0.2 = 0.4 m，才容得下 0.35 m 宽的
机器人（0.5 时通带为负，门口封死）。

**Q26. footprint 为什么重要？**
A：代价地图用 footprint 多边形做足迹碰撞检测（不用圆形近似），决定
"机器人能否通过"与路径的安全性；本项目 footprint 0.49×0.35 m 多边形。

**Q27. 为什么机器人会贴墙？**
A：本实验贴墙现象源于 AMCL 信念偏航误差（空闲漂移 + 走廊歧义）：信念
认为直行，实际斜向贴墙。修复：caster 摩擦消漂移 + 运动噪声趋零 +
匹配锐化。不是控制器本身缺陷。

**Q28. 为什么机器人过不了窄通道？**
A：两个叠加原因：① 膨胀半径 0.5 把 0.8 m 门口封死（通带为负）；② 车体
角落读数 (0.276 m) 穿透过滤阈值形成绕车自身障碍团。修复：膨胀 0.2 +
过滤 0.30 + DWB 短前瞻，R1 窄门口专项通过。

## 仿真与工程

**Q29. use_sim_time 为什么重要？**
A：让所有节点用 /clock（仿真时钟）而非墙钟，保证消息时间戳、TF 查询、
生命周期超时都在同一时间轴上；混用会导致 TF 外推失败、消息被拒。

**Q30. 什么是生命周期节点？**
A：可管理状态机（unconfigured→inactive→active）的节点，由
lifecycle_manager 统一配置/激活，使系统可按序启动、故障时可控降级。
Nav2 各节点均为生命周期节点。

**Q31. 你的复杂环境体现在哪里？**
A：16×12 m 四房间+长走廊+0.8 m 窄门口（通行极限）+U/L 形障碍+
激光遮挡区（R3 箱体后方盲区）+多独立箱体+危险区，5 个导航目标覆盖
全部挑战。

**Q32. 实验对比如何保证公平？**
A：① 同一 rosbag（582 s、50/50 航点）分别离线回放两算法（--clock +
use_sim_time）；② 同出生点同路线同运动数据；③ Cartographer 关 IMU 与
SLAM Toolbox 对齐；④ 量程参数一致；⑤ 地图为原始产物未清理；⑥ 导航
同参数、同目标、每图 3 轮共 30 次。

**Q33. 为什么不用主观"地图好看"来评价？**
A：地图质量用可量化指标（覆盖率、门口占用、走廊噪声、墙厚、断墙），
导航表现用成功率/耗时/恢复次数，全部由脚本采集生成 CSV/JSON，报告
由数据自动生成，结论不预设优劣。

**Q34. 最大的排障收获是什么？**
A：DDS QoS 兼容性（RELIABLE/BEST_EFFORT 不匹配会让订阅端静默失联，
无任何报错）——本项目 0/5 全败的根因；其次是仿真特有现象（空闲漂移、
本体烘焙进地图）需要物理层与数据层联合排查。

**Q35. 项目的已知局限？**
A：① 长路线导航成功率受 AMCL 走廊歧义限制（如实记录，非 SLAM 差异）；
② 过滤阈值 0.30 牺牲 0.30 m 内障碍感知（静态场景可接受）；③ 环境为
Humble/Classic，与计划 Jazzy/Harmonic 有偏差，已如实记录。
