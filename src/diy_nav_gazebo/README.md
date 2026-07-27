# diy_nav_gazebo

`diy_nav_bot` 的 Gazebo Classic 11 仿真包。

## 内容

| 目录 | 说明 |
|------|------|
| `worlds/` | Gazebo 世界文件（`.world` / `.sdf`） |
| `models/` | 自定义 Gazebo 模型（可选） |
| `launch/` | 启动 Gazebo + 机器人 + `robot_state_publisher` 的 launch 文件 |
| `config/` | Gazebo 客户端 GUI、物理引擎、传感器参数 YAML |
| `scripts/` | 辅助脚本（重置世界、录制话题等） |

## 状态

**骨架阶段（Phase 3）** — 尚未包含真实的世界或 launch。

## 构建

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select diy_nav_gazebo
```

## 依赖

- Gazebo Classic 11 + `gazebo_ros_pkgs` / `gazebo_plugins`
- `diy_nav_description`
