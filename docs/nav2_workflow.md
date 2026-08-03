# Nav2 工作流程与参数（nav2_workflow.md / nav2_parameters.md）

## 工作流程

### 启动顺序（bringup.launch.py mode:=navigation）

```text
仿真（gzserver → spawn → scan_filter）→ map_server → amcl → 生命周期管理
→（RViz 中设置初始位姿 / 脚本发布 /initialpose）→ 导航节点激活
```

关键依赖：AMCL 必须先收到初始位姿（map→odom 出现），costmap 的 TF 才
可用，生命周期激活才不卡死（本项目用“持续发布初始位姿 25s + 手动激活”
兜底）。

### 一次导航任务的执行链

1. 用户发送 NavigateToPose（Action，仿真时钟戳）
2. bt_navigator 行为树：Planner → Controller → 进度检查 →（失败则 Recovery）
3. planner_server：全局代价地图（static+obstacle+inflation）上 NavFn 搜索
4. controller_server：局部代价地图（rolling window）+ DWB 轨迹采样（20 前向
   ×20 角向）→ 最优轨迹的 /cmd_vel
5. velocity_smoother 限速限加速度 → 差速驱动执行
6. AMCL 每帧扫描校正 map→odom → 闭环

### 恢复行为
进度检查（10 s 位移 <0.5 m）失败 → Spin（360°）→ 仍失败 → BackUp → 重试；
恢复耗尽 → 目标 FAILED。

## 参数（config/nav2_params.yaml，阶段 10 调优后）

### AMCL
| 参数 | 值 | 说明 |
|------|----|------|
| alpha1-5 | 0.01 | 运动噪声趋零（仿真里程计为真值，防走廊锚漂移） |
| min/max_particles | 1000/3000 | 粒子数 |
| max_beams | 180 | 匹配波束（基线 60） |
| laser_likelihood_max_dist | 0.3 | 匹配锐度（基线 2.0，防贴墙扫描穿墙塌缩） |
| sigma_hit / z_hit | 0.1 / 0.7 | 命中高斯更尖、权重更高 |
| update_min_d / a | 0.1 / 0.1 | 更新阈值 |
| laser_max/min_range | 8.0 / 0.13 | 对齐激光量程 |

### 代价地图
| 参数 | 值 | 说明 |
|------|----|------|
| inflation_radius | 0.2 | 阶段 10 从 0.5 收缩（0.8 m 门口通带恢复 0.4 m） |
| cost_scaling_factor | 8.0 | 衰减更陡（远场代价降低） |
| robot_base_frame | base_footprint | 全部 |
| footprint | [[0.245,0.175],...] | 多边形，不用 robot_radius |
| obstacle_max/raytrace_range | 6.0/8.0 | 扫描 |
| global/local 更新频率 | 1.0/5.0 Hz | |

### DWB 控制器
| 参数 | 值 |
|------|----|
| max_vel_x / max_speed_xy | 0.22 |
| max_vel_theta | 1.0 |
| sim_time | 1.0（短前瞻，窄通道敏捷） |
| vx/vtheta_samples | 20/20 |
| xy_goal_tolerance | 0.35（容忍小信念误差） |

### velocity_smoother
max_velocity [0.22, 0, 1.0]，max_accel [2.5, 0, 3.2]，OPEN_LOOP 反馈。

### 调优记录
完整七字段日志见 `src/diy_nav_navigation/docs/nav2_tuning_log.md`
（3 轮：膨胀/速度 → 过滤阈值 0.30 → 运动噪声/容差；R1 窄门口打通；
成功率 2/5×3 轮，未达 80%，AMCL 走廊歧义为原理性限制，如实记录）。
