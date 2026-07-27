# diy_nav_description

`diy_nav_bot` 的机器人静态描述包。

## 内容

| 目录 | 说明 |
|------|------|
| `urdf/` | 机器人 URDF/Xacro 主文件与宏 |
| `meshes/` | 视觉/碰撞网格（可选） |
| `launch/` | 加载模型的 launch 文件（`robot_state_publisher` / `joint_state_publisher_gui` / RViz） |
| `rviz/` | 用于模型可视化的 RViz 配置 |

## 状态

**骨架阶段（Phase 3）** — 尚未包含真实的 URDF/Xacro，后续阶段（Phase 4）添加。

## 构建

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select diy_nav_description
```
