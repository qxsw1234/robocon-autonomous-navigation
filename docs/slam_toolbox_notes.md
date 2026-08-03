# SLAM Toolbox 建图笔记（slam_toolbox_notes.md）

## 1. 节点与数据流

```
/scan ──┐
/odom ──┼──> async_slam_toolbox_node ──> /map (nav_msgs/msg/OccupancyGrid, 2 s 更新)
/tf  ───┘                              └──> map → odom TF (50 Hz, transform_publish_period=0.02)
```

- 输入：`/scan`（10 Hz）、`/odom`（30 Hz）、TF 树（odom→base_footprint 由差速插件、
  base_footprint→laser_link 由 RSP）
- 输出：`/map`（栅格地图，分辨率 0.05 m/格）、`map → odom` TF
- 关键参数（`config/slam_toolbox.yaml`）：
  - `mode: mapping`（在线异步建图）
  - `resolution: 0.05`、`map_update_interval: 2.0`
  - `max_laser_range: 8.0`（对齐激光量程）、`min_laser_range: 0.13`（滤除车体自遮挡）
  - `do_loop_closing: true`（16 m 长走廊回环检测必须）
  - `minimum_travel_distance: 0.5` / `minimum_travel_heading: 0.5`（关键帧插入阈值）
  - `use_sim_time: true`

## 2. 为什么 SLAM 发布 map → odom 而不是 odom → map

TF 树的"根"是 `map`（全局坐标系）。SLAM 把激光扫描匹配到全局地图后，
得到的是**机器人（经由 odom 树）在地图中的位姿**，因此它发布的是
`map → odom`（map 是父帧）。这样：

- `odom → base_footprint` 仍由里程计（差速插件）负责——**保持单一来源**，
  即使 SLAM/AMCL 挂了，机器人内部 TF 树依然完整；
- `map → odom` 表达了"里程计原点在地图中的位置"，SLAM 回环修正只会
  改变 `map → odom`，不会破坏 odom 以下的局部一致性。

**互斥约束**：同一时刻只允许一个节点发布 `map → odom`
（slam_toolbox / cartographer / AMCL 三选一），否则 TF 抖动。

## 3. /scan + /odom → /map 的关系

- 帧间匹配（scan matching）：用当前 `/scan` 与滑动窗口（`scan_buffer_size: 10`）
  内最近的关键帧匹配，得到相对位姿增量；
- 里程计先验：`/odom` 提供匹配的初始猜测（scan-to-scan 加 odometry 的经典 Karto 流程）；
- 回环检测：窗口之外的候选帧（`loop_search_maximum_distance: 3.0`）在
  `loop_search_space_dimension: 8.0` 范围内粗搜+细搜，命中后做图优化
  （Ceres solver），把累积漂移拉回；
- 地图更新：优化后的位姿栅格化进 `/map`，`map_update_interval: 2.0` 控制发布频率。

## 4. 参数作用速查（改动最多的一组）

| 参数 | 作用 | 本工程取值 |
|------|------|-----------|
| `minimum_travel_distance` | 位移超过该值才插入关键帧 | 0.5 m |
| `minimum_travel_heading` | 转角超过该值才插入关键帧 | 0.5 rad |
| `scan_buffer_size` | 滑动窗口大小 | 10 |
| `do_loop_closing` | 回环检测开关 | true |
| `loop_match_minimum_chain_size` | 回环最小链长（防误检） | 10 |
| `loop_match_minimum_response_*` | 回环匹配响应阈值（粗/细） | 0.35 / 0.45 |
| `correlation_search_space_dimension` | 帧间匹配搜索范围 | 0.5 m |
| `loop_search_space_dimension` | 回环搜索范围 | 8.0 m |
| `transform_publish_period` | map→odom 发布周期 | 0.02 s（50 Hz） |
| `min_laser_range` | 滤除过近读数（自遮挡） | 0.13 m |

## 5. 建图流程与实测

```bash
# 1) 仿真（complex 世界）
ros2 launch diy_nav_gazebo simulation.launch.py world:=complex headless:=true rviz:=false
# 2) SLAM
ros2 launch diy_nav_navigation slam_toolbox.launch.py rviz:=false
# 3) 自动巡航（外圈→逐房间→窄门口慢行→回起点闭环，约 15 min）
python3 ~/ros2_ws/src/diy_nav_navigation/scripts/mapping_tour.py
# 4) 保存地图
ros2 run nav2_map_server map_saver_cli \
  -f ~/ros2_ws/src/diy_nav_navigation/maps/complex_slam_toolbox
```

实测结果：48 个航点全部 PASS，闭环回到起点；地图保存为
`maps/complex_slam_toolbox.pgm` + `.yaml`。

## 6. 实际遇到的问题

1. **首帧被丢弃**：`Message Filter dropping message ... earlier than all the data in
   the transform cache`——launch 启动瞬间 TF 缓存为空，SLAM 就绪后自动恢复，无需处理。
2. **车体自遮挡进地图**：激光平面（0.23 m）与上盖顶（0.215 m）间隙仅 1.5 cm，
   俯仰瞬态会读到 0.12 m（range_min 盲区）。处理：`min_laser_range: 0.13` 过滤。
3. **回环质量依赖速度**：巡航采用线速 0.25 m/s、角速上限 0.6 rad/s、转弯降速，
   保证扫描重叠率；若建图质量不足，可进一步降速或改手动 teleop。
