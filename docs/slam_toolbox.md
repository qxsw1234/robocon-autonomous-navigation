# SLAM Toolbox（slam_toolbox.md）

## 概述

在线异步 2D SLAM（slam_toolbox 2.6.10），基于 Ceres 图优化 + 扫描匹配 +
回环检测。本项目用作第一建图方案（阶段 8），配置以官方
`mapper_params_online_async.yaml` 为基线。

## 关键参数（config/slam_toolbox.yaml）

| 参数 | 值 | 说明 |
|------|----|------|
| scan_topic | /scan_slam | RELIABLE 双发布通道（QoS 排障产物） |
| mode | mapping | 在线异步建图 |
| solver_plugin | CeresSolver | 图优化求解器 |
| map_update_interval | 2.0 s | 地图发布周期 |
| resolution | 0.05 | 栅格分辨率 |
| min/max_laser_range | 0.13 / 8.0 | 对齐激光与过滤器 |
| minimum_travel_distance | 0.5 | 扫描插入阈值 |
| do_loop_closing | true | 回环检测 |
| scan_buffer_size | 10 | 扫描缓冲（回环匹配） |
| enable_interactive_mode | false | 关闭交互（无手动修正） |

## 工作流程

```text
/scan_slam + /odom + TF
  → 扫描匹配（相关性匹配 + Ceres 精配）
  → 位姿图插入（运动距离/角度阈值）
  → 回环搜索（scan_buffer 内，响应阈值 0.35/0.45）
  → 图优化 → /map 发布（2 s 周期）
```

## 建图实测（阶段 8，complex 世界）

- 50 航点路线完成率 50/50（580 s）
- 四门口占用 R1 8% / R2 6% / R3 7% / R4 7%（在线）——可通行
- 特点：走廊干净（噪声 59 格），但转点处车体角落读数会烘焙出 0.4×0.4
  幽灵块（过滤阈值 0.30 后消失，地图经连通域清理）

## 常见问题

- `map_saver_cli` 在本环境偶发 "Failed to spin map subscription" → 用
  `save_map.py`（transient_local 直取 /map latch）
- 扫描 QoS：必须订阅 /scan_slam（RELIABLE），/scan 为 BE 不保证兼容
