# diy_nav_gazebo

`diy_nav_bot` 的 Gazebo Classic 11 仿真包：世界文件、仿真 launch、插件参数与测试脚本。

## 内容

| 目录 | 说明 |
|------|------|
| `worlds/` | 三个自建世界：`empty_world` / `simple_world` / `complex_world`（纯 SDF 基本几何体，零 Fuel 依赖） |
| `launch/` | `simulation.launch.py`：启动 Gazebo + 机器人 + robot_state_publisher（可选 RViz） |
| `config/` | `gazebo_params.yaml`：插件可调参数总表（与 `gazebo_plugins.xacro` 同步） |
| `rviz/` | `simulation.rviz`：Grid + TF + RobotModel + LaserScan + Odometry |
| `scripts/` | `test_motion.sh`：差速运动验收（前进/旋转/停止漂移） |

## 启动仿真

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

# 空世界（运动测试底稿）
ros2 launch diy_nav_gazebo simulation.launch.py

# 简单世界 / 复杂世界（简写即可，无需绝对路径）
ros2 launch diy_nav_gazebo simulation.launch.py world:=simple
ros2 launch diy_nav_gazebo simulation.launch.py world:=complex

# 自动化测试常用：无 GUI、无 RViz
ros2 launch diy_nav_gazebo simulation.launch.py world:=complex headless:=true rviz:=false
```

launch 参数：`world`（empty|simple|complex 或 .world 绝对路径）、`x/y/z/yaw`（出生位姿）、
`rviz`（默认 true）、`headless`（默认 false）、`use_sim_time`（默认 true）。

## 世界说明

### simple_world（10×8 m，x∈[-5,5]，y∈[-4,4]）

四周外墙 + 中央障碍 + 直角弯（L 形转角走廊）+ 2 独立箱体 + 起点区 + 3 目标区 + 危险区。
所有通道宽度 ≥ 1.0 m，适合基础导航与运动测试。

### complex_world（16×12 m，x∈[-8,8]，y∈[-6,6]）

- **16 m 长直走廊**（宽 1.5 m）：激光特征高度相似，刻意考验 SLAM 回环检测
- **多房间**：上排 R1/R2、下排 R3/R4（房间分隔墙），门口 R1 宽 **0.8 m**（窄通道考验）、R2 宽 1.2 m、R3/R4 宽 1.0 m
- **U 形障碍**（R2）、**L 形障碍**（R4）、**遮挡大箱体**（R3，背后形成激光遮挡区）、多独立箱体
- 走廊 + 房间构成多条回环路线；起点区 + 6 目标区 + 危险区

### 世界材质（6 组，便于录像区分）

| 元素 | 颜色 | 说明 |
|------|------|------|
| 地面 | 浅灰 | 地面平面 |
| 墙 | 蓝灰 | 外墙 / 走廊墙 / 房间分隔墙 |
| 障碍 | 橙 | 中央障碍、U/L 形障碍、箱体、遮挡箱 |
| 危险区 | 红 | 地面薄标记（**无碰撞**） |
| 起点 | 绿 | 地面薄标记（**无碰撞**） |
| 目标 | 黄 | 薄圆柱 r=0.18 m（**无碰撞**，不挡激光） |

## 推荐初始位姿与目标点

两世界的起点区均位于原点，launch 默认出生位姿 `x=0 y=0 z=0.1 yaw=0` 即为推荐位姿。

### simple_world 目标点

| 编号 | 坐标 (x, y) | 位置描述 |
|------|------------|----------|
| G1 | (3.4, 2.8) | 东北角，箱体 A 旁 |
| G2 | (-3.6, 2.6) | 西北角，直角弯北侧 |
| G3 | (-3.0, -3.2) | 西南角，箱体 B 附近 |

### complex_world 目标点

| 编号 | 坐标 (x, y) | 位置描述 |
|------|------------|----------|
| G1 | (6.5, 4.5) | R2 东北角，U 形障碍东侧 |
| G2 | (-6.5, 4.5) | R1 西北角 |
| G3 | (-6.5, -4.5) | R3 西南角，遮挡箱体西侧 |
| G4 | (6.5, -4.5) | R4 东南角，L 形障碍东侧 |
| G5 | (-7.5, 0.0) | 走廊西端 |
| G6 | (7.5, 0.0) | 走廊东端 |

## 验收测试

```bash
# 运动验收（需仿真已启动）：前进/原地旋转/停止不漂移，3 项全 PASS 退出码 0
bash ~/ros2_ws/src/diy_nav_gazebo/scripts/test_motion.sh
```

## 构建

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select diy_nav_gazebo
```

## 依赖

- Gazebo Classic 11 + `gazebo_ros_pkgs` / `gazebo_plugins`
- `diy_nav_description`
