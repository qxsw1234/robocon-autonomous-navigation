#!/usr/bin/env bash
# ----------------------------------------------------------------------
# validate_simulation.sh — 仿真接口与 TF 验收（阶段 7）
# ----------------------------------------------------------------------
# 前置条件：simulation.launch.py 已启动且机器人已生成。
# 用法：
#   bash ~/ros2_ws/src/diy_nav_gazebo/scripts/validate_simulation.sh
#
# 检查项：
#   1. 9 个必备 topic 存在 + 消息类型正确
#   2. 输出类 topic 均有发布者
#   3. 关键 topic 频率达标（/scan≈10Hz /odom≈30Hz /imu≈50Hz）
#   4. TF 连通：odom→base_footprint / base_footprint→laser_link / →left_wheel_link
#   5. 重复 TF 检测：/tf 必须恰好 2 个发布者
#      （robot_state_publisher + diy_diff_drive，odom→base_footprint 唯一来源）
# 单项失败不中断，末尾汇总退出码。
# ----------------------------------------------------------------------
set -uo pipefail

GREP=/usr/bin/grep

if [ -z "${ROS_DISTRO:-}" ]; then
  source /opt/ros/humble/setup.bash
fi
if ! ros2 pkg prefix diy_nav_gazebo >/dev/null 2>&1; then
  source "${HOME}/ros2_ws/install/setup.bash"
fi

FAILS=0
WARNS=0
pass()  { printf '[PASS] %s\n' "$*"; }
warn()  { printf '[WARN] %s\n' "$*"; WARNS=$((WARNS+1)); }
fail()  { printf '[FAIL] %s\n' "$*"; FAILS=$((FAILS+1)); }

# ---------------- 1. 必备 topic + 类型 ----------------
# topic:期望类型
REQUIRED_TOPICS=(
  "/clock:rosgraph_msgs/msg/Clock"
  "/cmd_vel:geometry_msgs/msg/Twist"
  "/odom:nav_msgs/msg/Odometry"
  "/tf:tf2_msgs/msg/TFMessage"
  "/tf_static:tf2_msgs/msg/TFMessage"
  "/joint_states:sensor_msgs/msg/JointState"
  "/scan:sensor_msgs/msg/LaserScan"
  "/imu:sensor_msgs/msg/Imu"
  "/robot_description:std_msgs/msg/String"
)

echo "[INFO] === 1. 必备 topic 与类型 ==="
for entry in "${REQUIRED_TOPICS[@]}"; do
  topic="${entry%%:*}"
  want="${entry##*:}"
  got="$(ros2 topic type "${topic}" 2>/dev/null || true)"
  if [ -z "${got}" ]; then
    fail "topic ${topic} 不存在"
  elif [ "${got}" = "${want}" ]; then
    pass "topic ${topic} 类型=${got}"
  else
    fail "topic ${topic} 类型=${got}（期望 ${want}）"
  fi
done

# ---------------- 2. 输出类 topic 均有发布者 ----------------
echo "[INFO] === 2. 发布者检查 ==="
for topic in /clock /odom /tf /tf_static /joint_states /scan /imu /robot_description; do
  count="$(ros2 topic info "${topic}" 2>/dev/null | "${GREP}" -oP 'Publisher count: \K\d+' || true)"
  if [ -n "${count}" ] && [ "${count}" -ge 1 ]; then
    pass "topic ${topic} 发布者=${count}"
  else
    fail "topic ${topic} 无发布者"
  fi
done

# ---------------- 3. 频率检查（rclpy 实测 5 s） ----------------
echo "[INFO] === 3. 频率检查（5 s 采样） ==="
python3 - <<'PY'
import sys
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, JointState, Imu
from nav_msgs.msg import Odometry

EXPECT = {'/scan': (8, 12), '/odom': (24, 36), '/imu': (40, 60)}
TYPES = {'/scan': LaserScan, '/odom': Odometry, '/imu': Imu}

class Probe(Node):
    def __init__(self):
        super().__init__('validate_freq_probe')
        self.counts = {t: 0 for t in EXPECT}
        for t, ty in TYPES.items():
            self.create_subscription(ty, t, lambda m, t=t: self._cb(t), 50)
    def _cb(self, topic):
        self.counts[topic] += 1

rclpy.init()
p = Probe()
t0 = time.time()
while time.time() - t0 < 5.0:
    rclpy.spin_once(p, timeout_sec=0.1)
dt = time.time() - t0
fails = 0
for t, (lo, hi) in EXPECT.items():
    hz = p.counts[t] / dt
    if lo <= hz <= hi:
        print(f'[PASS] {t} 频率={hz:.1f} Hz（期望 {lo}~{hi}）')
    else:
        print(f'[FAIL] {t} 频率={hz:.1f} Hz（期望 {lo}~{hi}）')
        fails += 1
rclpy.shutdown()
sys.exit(1 if fails else 0)
PY
[ $? -eq 0 ] || FAILS=$((FAILS+1))

# ---------------- 4. TF 连通 ----------------
echo "[INFO] === 4. TF 连通 ==="
tf_check() {
  local parent="$1" child="$2"
  # 注意：tf2_echo 不会自行退出，timeout 必然 SIGTERM；
  # 先捕获输出再 grep，避免 pipefail + SIGPIPE 造成的假阴性。
  local out
  out="$(timeout 8 ros2 run tf2_ros tf2_echo "${parent}" "${child}" 2>/dev/null || true)"
  if printf '%s' "${out}" | "${GREP}" -qm1 "Translation"; then
    pass "TF ${parent} -> ${child} 连通"
  else
    fail "TF ${parent} -> ${child} 不可达"
  fi
}
tf_check odom base_footprint
tf_check base_footprint laser_link
tf_check base_footprint left_wheel_link

# ---------------- 5. 重复 TF 检测 ----------------
echo "[INFO] === 5. 重复 TF 检测（odom→base_footprint 唯一来源） ==="
# 只统计 Endpoint type: PUBLISHER 块对应的 Node name
TF_PUBS="$(ros2 topic info /tf -v 2>/dev/null | \
  awk '/Node name:/{n=$3} /Endpoint type: PUBLISHER/{print n}' | sort -u)"
echo "[INFO] /tf 发布者: ${TF_PUBS}"
EXPECT_PUBS="diy_diff_drive
robot_state_publisher"
if [ "${TF_PUBS}" = "${EXPECT_PUBS}" ]; then
  pass "/tf 恰好 2 个发布者（robot_state_publisher + diy_diff_drive），odom→base_footprint 无重复"
else
  fail "/tf 发布者集合异常（期望 robot_state_publisher + diy_diff_drive，实际: ${TF_PUBS}）"
fi

# 额外：从 /tf 消息中确认 odom→base_footprint 对存在
if timeout 8 ros2 topic echo /tf --once 2>/dev/null | "${GREP}" -q "child_frame_id: base_footprint"; then
  pass "/tf 消息中存在 odom→base_footprint"
else
  fail "/tf 消息中未发现 base_footprint 子帧"
fi

# ---------------- 汇总 ----------------
echo ""
echo "===================================================="
if [ "${FAILS}" -eq 0 ]; then
  echo "VALIDATE SIMULATION SUMMARY: ${FAILS} FAIL, ${WARNS} WARN -> OK"
  exit 0
else
  echo "VALIDATE SIMULATION SUMMARY: ${FAILS} FAIL, ${WARNS} WARN -> FAILED"
  exit 1
fi
