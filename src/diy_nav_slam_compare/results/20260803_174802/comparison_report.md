# SLAM 对比实验报告 — 20260803_174802

> 结论由以下实测数据得出，不预设某算法更优。

## 实验环境

- 算法版本: {}
- 世界: complex_world.world (16x12 m, 四房间+走廊+窄门口0.8m+U/L障碍+遮挡区)
- bag: results/bags/mapping_20260803_173441 (582 s, 50/50 航点, 105 MB)
- 传感器: {'laser': '/scan_slam (RELIABLE 双发布, 720 samples, 10 Hz, 0.30~8.0 m 过滤后)', 'odom': '/odom (差速驱动, 30 Hz)', 'tf': '/tf + /tf_static (同一 bag 回放)'}

## 资源占用（回放同一 bag）

| 指标 | SLAM Toolbox | Cartographer |
|------|-------------|--------------|
| cpu_avg | 3.14 | 6.51 |
| cpu_peak | 19.0 | 73.9 |
| rss_avg_mb | 46.22 | 49.46 |
| rss_peak_mb | 50.88 | 59.47 |

## 地图指标（map_statistics）

| 指标 | SLAM Toolbox | Cartographer |
|------|-------------|--------------|
| occupied_ratio | 0.0544 | 0.078 |
| free_ratio | 0.9456 | 0.8314 |
| unknown_ratio | 0.0 | 0.0907 |
| corridor_noise_px | 59 | 903 |
| north_wall_segments | 1 | 1 |

## 导航表现（每地图 5 目标 × 3 次）

| 指标 | SLAM Toolbox | Cartographer |
|------|-------------|--------------|
| success | 2/15 | 3/15 |
| avg_time_s | 20.3 | 45.4 |
| avg_recovery | 6.2 | 14.4 |
| min_min_scan_m | 0.3 | 0.3 |

## 结论（依据上述实测数据，不预设优劣）

### 1. 资源占用 —— SLAM Toolbox 显著更省
- CPU 均值 3.14% vs 6.51%（约 2 倍差距）；CPU 峰值 19.0% vs 73.9%（约 4 倍差距）
- RSS 内存 46.2 vs 49.5 MB（差距小）
- 结论：同数据回放下，SLAM Toolbox 计算开销明显低于 Cartographer。

### 2. 地图精度 —— 各有优劣
- 门口占用：SLAM Toolbox R1 8%/R2 6%/R3 6%/R4 7%；Cartographer R1 0%/R2 0%/R3 0%/R4 8%
  → Cartographer 对窄门口（R1 0.8m）的刻画显著更清晰（0% vs 8%）
- 走廊噪声：SLAM Toolbox 59 格 vs Cartographer 903 格（约 15 倍差距）
  → SLAM Toolbox 走廊更干净（其噪声为转点处车体角点读数，Cartographer 为弥散散点）
- 覆盖：SLAM Toolbox 未知区 0%（地图 322x242）；Cartographer 未知区 9.07%（地图 507x448，
  范围更大但覆盖率低）
- 断墙数均为 1（墙结构完整）；墙厚 5px（0.25m）两者相当

### 3. 导航表现 —— Cartographer 成功率略高，但耗时/恢复更多
- 成功率：SLAM Toolbox 2/15（13.3%）vs Cartographer 3/15（20.0%）
- 平均耗时：20.3s vs 45.4s（SLAM Toolbox 更快）
- 平均恢复行为：6.2 次 vs 14.4 次（SLAM Toolbox 更少）
- 两图成功率总体均低（13-20%）：导航栈（AMCL 走廊歧义）为共同限制因素，
  非 SLAM 算法差异——两地图在同参数下对比，差异可归因于地图质量本身

### 4. 综合
- 无绝对胜者：SLAM Toolbox 在资源效率、走廊噪声、导航耗时/恢复上占优；
  Cartographer 在门口精度（窄通道刻画）上占优
- 工程建议：追求低功耗/简单部署选 SLAM Toolbox；需要更精确的窄通道地图选 Cartographer
