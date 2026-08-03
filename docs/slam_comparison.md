# SLAM 对比实验（slam_comparison.md）

> 完整数据与报告见
> `src/diy_nav_slam_compare/results/20260803_174802/comparison_report.md`

## 公平性设计

1. **同一 rosbag 输入**：一次 582 s 建图路线（50/50 航点）录制
   `/scan_slam /odom /tf /tf_static /joint_states /imu /clock /cmd_vel`，
   两算法分别离线回放（`--clock` 提供仿真时间，全部 use_sim_time=true）
2. 同出生点、同路线、同运动数据
3. Cartographer `use_imu_data=false` 与 SLAM Toolbox 对齐（都只用激光+里程计）
4. min/max_range 均 0.30/8.0
5. 地图为离线回放原始产物（未清理），导航试验直接使用
6. 导航：同一 nav2_params.yaml、同 5 目标、每地图 3 轮（共 30 次）

## 8 项指标实测结果

| 指标 | SLAM Toolbox | Cartographer |
|------|-------------|--------------|
| 建图耗时（回放） | 582 s（同一 bag） | 582 s（同一 bag） |
| CPU 均值 / 峰值 | 3.14% / 19.0% | 6.51% / 73.9% |
| RSS 均值 / 峰值 | 46.2 / 50.9 MB | 49.5 / 59.5 MB |
| 地图覆盖（占用/空闲/未知） | 5.4% / 94.6% / 0% | 7.8% / 83.1% / 9.1% |
| 清晰度（墙厚 px / 走廊噪声） | 5.0 px / 59 格 | 5.0 px / 903 格 |
| 回环表现（起点双墙/断墙） | 断墙 1（无跳变） | 断墙 1（无跳变） |
| 参数复杂度 | 1 YAML，~50 参数 | 1 Lua（include 2 基线），~40 参数 |
| 导航成功率 / 平均耗时 / 恢复 | 2/15，20.3 s，6.2 次 | 3/15，45.4 s，14.4 次 |

## 结论（数据驱动，不预设优劣）

**SLAM Toolbox 优势**：计算开销显著低（CPU 均值约 1/2、峰值约 1/4）；
走廊噪声少（59 vs 903）；导航耗时与恢复行为更少；配置直观、启动简单。

**SLAM Toolbox 不足**：窄门口（0.8 m）刻画差（占用 8% vs 0%）——转点处
车体角落读数烘焙（已用过滤 0.30 缓解但残留）；导航成功率略低（2/15）。

**Cartographer 优势**：门口/窄通道地图精度显著更高（R1 0%）；地图范围
更大（507×448 vs 322×242）；导航成功率略高（3/15）。

**Cartographer 不足**：计算开销大（CPU 峰值 73.9%）；走廊弥散噪声多 15 倍；
地图未知区 9.1%（覆盖完整度低）；导航平均耗时 2 倍+、恢复行为 2.3 倍。

**在当前差速机器人、2D 激光、复杂室内环境下**：
- 若关注低功耗、部署简单、导航效率 → 推荐 **SLAM Toolbox**
- 若关注窄通道地图精度、愿意付出计算代价 → 推荐 **Cartographer**
- 两算法成功率均受共用导航栈（AMCL 走廊歧义）限制（13-20%），该限制
  不归因于 SLAM 算法本身，已在 nav2_tuning_log.md 如实记录

## 可复现

```bash
# 录 bag（需仿真）
bash src/diy_nav_slam_compare/scripts/record_mapping_bag.sh
# 离线回放（各 ~10 min，自动生成 results/时间戳/）
bash src/diy_nav_slam_compare/scripts/playback_slam_toolbox.sh <bag>
bash src/diy_nav_slam_compare/scripts/playback_cartographer.sh <bag>
# 导航试验（每地图 ~25 min）
bash src/diy_nav_slam_compare/scripts/run_nav_trials.sh slam_toolbox
bash src/diy_nav_slam_compare/scripts/run_nav_trials.sh cartographer
# 报告
python3 src/diy_nav_slam_compare/scripts/generate_report.py --experiment-dir <时间戳目录>
```
