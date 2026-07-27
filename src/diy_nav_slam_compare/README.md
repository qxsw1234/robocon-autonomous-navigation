# diy_nav_slam_compare

`diy_nav_bot` 的 SLAM 对比工具包（SLAM Toolbox vs Cartographer）。

## 内容

| 目录 | 说明 |
|------|------|
| `diy_nav_slam_compare/` | Python 源码（`cli.py` 等） |
| `launch/` | 启动两种 SLAM 的对比 launch |
| `config/` | SLAM Toolbox / Cartographer 参数（YAML / Lua） |
| `scripts/` | 数据录制/回放、指标提取脚本 |
| `results/` | 建图结果输出目录（`raw/` 会被 .gitignore） |
| `resource/` | ament index 资源标记文件 |

## Console scripts

| 命令 | 入口 |
|------|------|
| `slam_compare_cli` | `diy_nav_slam_compare.cli:main` |

骨架阶段仅提供占位 CLI，后续阶段将新增比较节点。

## 状态

**骨架阶段（Phase 3）** — CLI 可运行但为占位实现。

## 构建

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select diy_nav_slam_compare
source install/setup.bash
ros2 run diy_nav_slam_compare slam_compare_cli
```
