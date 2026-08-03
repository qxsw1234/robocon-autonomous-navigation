# 机器人模型（robot_model.md）

## 规格（diy_nav_description/urdf/properties.xacro 为唯一尺寸源）

| 部件 | 尺寸 | 质量 | 说明 |
|------|------|------|------|
| 底盘 | 0.45 × 0.32 × 0.12 m | 8.0 kg | 质心位于几何中心 |
| 上盖 | 0.24 × 0.20 × 0.02 m | 0.3 kg | 阶段 4.5 收薄（原 0.08），使激光平面高于车体顶面 |
| 驱动轮 | r=0.075, 宽 0.035 | 0.6 kg ×2 | 轮线 x 偏移 −0.08 m（稳定裕度） |
| 前万向轮 | r=0.035（球） | 0.15 kg | x 偏移 +0.19 m |
| 激光雷达 | 安装高 0.23 m | — | 720 线 / 10 Hz / 0.12~8.0 m / σ=0.01 |
| IMU | 底盘中心 | — | 50 Hz |

## 稳定裕度设计（阶段 9 排障记录）

- 轮线在质心后方 0.082 m → 前翻角 atan(0.082/0.15) ≈ **28.7°**；
  早期 −0.04 m 版仅 15.7°，急转/减速即前翻（车体灌入激光平面污染地图）
- 万向轮承重 ~30%（早期 ~1.4% 时临界稳定，任意扰动后翻）
- caster mu=0.05（阶段 10）：零摩擦无偏航约束，ODE 抖动致 ~2°/min 空闲漂移；
  0.05 阻尼漂移（3 分钟静止仅 0.007°）又不妨碍原地旋转

## TF 与 Link/Joint（REP-103）

```text
base_footprint                （地面投影，z=0）
└── base_link                 （底盘质心系，z=0.135）
    ├── left_wheel_link        left_wheel_joint    continuous
    ├── right_wheel_link       right_wheel_joint   continuous
    ├── front_caster_link      front_caster_joint  fixed
    ├── laser_link             laser_joint         fixed
    └── imu_link               imu_joint           fixed
```

## Gazebo 插件（gazebo_plugins.xacro）

| 插件 | 配置 |
|------|------|
| 差速驱动 | 轮距 0.36 m，30 Hz，publish_odom_tf=true，publish_wheel_tf=false |
| 2D 激光 | /scan_raw，720 线，10 Hz，0.12~8.0 m，σ=0.01 |
| IMU | 50 Hz（必须 `<always_on>true</always_on>`） |
| 关节状态 | /joint_states |
| 摩擦 | 轮 mu=1.0 kp=1e8 kd=1.0；caster mu=0.05 |

## 自遮挡抑制（scan_filter.py）

激光平面 0.23 m 与车体顶面间隙小：车体正面 0.225 m、侧面 0.16 m、角落
0.276 m。过滤器把 < 0.30 m 的读数置 inf（阶段 10 升级：0.30 覆盖角落读数，
否则实时代价地图出现绕车 0.5 m 自身障碍团堵死窄门口）。代价：0.30 m 内
真实障碍不可见（R1 门框 0.22 m 读数被滤，但物理余量 0.225 m 足够通过）。

## 验证（validate_description.sh）

xacro 展开 → check_urdf → 9 话题/类型/频率/TF 唯一性全绿。
