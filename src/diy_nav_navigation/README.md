# diy_nav_navigation

`diy_nav_bot` 的 Navigation2 配置与启动包。

## 内容

| 目录 | 说明 |
|------|------|
| `launch/` | Nav2 bringup、AMCL 定位、localisation 启动文件 |
| `config/` | Nav2 全参数 YAML（planner / controller / bt_navigator / behavior / costmap 等） |
| `maps/` | 静态占用栅格地图（`.yaml` + `.pgm`） |
| `rviz/` | 导航专用 RViz 配置 |
| `behavior_trees/` | 自定义 BehaviorTree XML |

## 状态

**骨架阶段（Phase 3）** — 尚未包含实际参数或地图。

## 构建

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select diy_nav_navigation
```
