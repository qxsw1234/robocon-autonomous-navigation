# Nav2 参数说明（nav2_parameters.md）

> 详细调优过程与七字段日志见 `src/diy_nav_navigation/docs/nav2_tuning_log.md`
> 与 `nav2_workflow.md`。本文件为参数总览。

## 文件位置

- `src/diy_nav_navigation/config/nav2_params.yaml`（当前生效，阶段 10 调优后）
- `src/diy_nav_navigation/config/nav2_params_stage10_backup.yaml`（调优前备份）
- `src/diy_nav_navigation/config/slam_toolbox.yaml`（SLAM Toolbox）

## 参数分组（7 组）

| 组 | 关键参数 | 当前值 | 调优原因 |
|----|---------|--------|---------|
| 运动限制 | max_vel_x / max_speed_xy | 0.22 | 0.26 太快，窄通道反应不及 |
| footprint | 多边形 0.49×0.35 m | 4 点 | 不用 robot_radius（更精确） |
| 障碍层 | obstacle_max_range / raytrace_max_range | 6.0 / 8.0 | 对齐激光 |
| 膨胀层 | inflation_radius / cost_scaling_factor | 0.2 / 8.0 | 0.5 封死 0.8 m 门口 |
| 规划器 | NavfnPlanner / allow_unknown | tolerance 0.5 | 官方默认 |
| 控制器 | DWB sim_time / 采样数 / 容差 | 1.0 / 20×20 / 0.35 | 短前瞻 + 容忍小信念误差 |
| 行为树 | 恢复行为 spin/backup | 默认 | 官方默认 |

## AMCL 参数（长路线稳定性的关键）

- alpha1-5 = 0.01：仿真里程计为真值，粒子紧贴里程计，防止走廊锚漂移
- laser_likelihood_max_dist = 0.3：匹配锐化，防贴墙扫描穿墙塌缩
- max_beams = 180、粒子 1000/3000：匹配充分
- update_min_d/a = 0.1：小幅运动即更新（map→odom 不长期过期）

## 验证方法

改参数 → 重启对应节点 → `nav_goal_runner.py` 5 目标测试 → 记录成功率/
耗时/恢复/最小激光 → 写入调优日志（七字段）。
