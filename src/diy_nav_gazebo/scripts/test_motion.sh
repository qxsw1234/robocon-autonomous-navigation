#!/usr/bin/env bash
# ----------------------------------------------------------------------
# test_motion.sh — 差速驱动运动验收测试（阶段 5）
# ----------------------------------------------------------------------
# 前置条件：simulation.launch.py 已启动且机器人已生成（/odom 有数据）。
# 用法：
#   bash ~/ros2_ws/src/diy_nav_gazebo/scripts/test_motion.sh
#
# 测试项（全部从 /odom 读数判定，不依赖目视）：
#   1. 前进：0.3 m/s × 2 s → 位移 ≈ 0.6 m（容差 ±20%）
#   2. 原地旋转：1.0 rad/s × π s → 偏航 ≈ +π（容差 ±20%）
#   3. 停止漂移：松指令 2 s → 位移 < 3 cm、偏航 < 0.05 rad
# 任一项 FAIL 时退出码非零。
# ----------------------------------------------------------------------
set -uo pipefail

# 环境（若未 source 则补上）
if [ -z "${ROS_DISTRO:-}" ]; then
  source /opt/ros/humble/setup.bash
fi
if ! ros2 pkg prefix diy_nav_gazebo >/dev/null 2>&1; then
  source "${HOME}/ros2_ws/install/setup.bash"
fi

echo "[INFO] test_motion.sh 开始（等待 /odom 与 /cmd_vel ...）"

python3 - <<'PY'
import math
import sys
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


def wrap(yaw0, yaw1):
    d = yaw1 - yaw0
    return (d + math.pi) % (2.0 * math.pi) - math.pi


class MotionTester(Node):
    def __init__(self):
        super().__init__('motion_tester')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pose = None  # (x, y, yaw)
        self.create_subscription(Odometry, '/odom', self._on_odom, 10)
        self._wait_first_odom()

    def _on_odom(self, msg):
        q = msg.pose.pose.orientation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                         1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        self.pose = (msg.pose.pose.position.x, msg.pose.pose.position.y, yaw)

    def _spin(self, seconds):
        """spin_once 驱动回调，持续 seconds 秒。"""
        t0 = time.time()
        while time.time() - t0 < seconds:
            rclpy.spin_once(self, timeout_sec=0.05)

    def _wait_first_odom(self, timeout=15.0):
        t0 = time.time()
        while self.pose is None:
            if time.time() - t0 > timeout:
                raise RuntimeError('超时：/odom 无数据（仿真是否已启动？）')
            rclpy.spin_once(self, timeout_sec=0.1)

    def sample(self):
        return self.pose

    def run_cmd(self, linear, angular, duration):
        """发布指令 duration 秒（期间持续 spin），返回 (位移, 偏航变化)。"""
        start_pose = self.sample()
        t0 = time.time()
        while time.time() - t0 < duration:
            tw = Twist()
            tw.linear.x = linear
            tw.angular.z = angular
            self.pub.publish(tw)
            self._spin(0.05)
        self.stop()
        end_pose = self.sample()
        dx = end_pose[0] - start_pose[0]
        dy = end_pose[1] - start_pose[1]
        return math.hypot(dx, dy), wrap(start_pose[2], end_pose[2])

    def stop(self):
        self.pub.publish(Twist())

    def stop_and_wait(self, duration):
        self.stop()
        self._spin(duration)
        return self.sample()


def main():
    rclpy.init()
    tester = MotionTester()
    fails = 0

    def check(name, ok, detail):
        nonlocal fails
        tag = '[PASS]' if ok else '[FAIL]'
        print(f'{tag} {name}: {detail}')
        if not ok:
            fails += 1

    # 1. 前进
    dist, _ = tester.run_cmd(0.3, 0.0, 2.0)
    check('前进 0.3m/s×2s', 0.48 <= dist <= 0.72,
          f'实测位移 {dist:.3f} m（期望 ≈0.6，容差 ±20%）')

    # 2. 原地左转（正角速度 = 逆时针）
    _, dyaw = tester.run_cmd(0.0, 1.0, math.pi)
    check('原地旋转 1.0rad/s×πs', 2.51 <= abs(dyaw) <= 3.77,
          f'实测偏航 {dyaw:.3f} rad（期望 ≈{math.pi:.3f}，容差 ±20%）')

    # 3. 停止漂移
    p0 = tester.stop_and_wait(2.0)
    dx = p0[0] - tester.pose[0]
    dy = p0[1] - tester.pose[1]
    dyaw = wrap(p0[2], tester.pose[2])
    drift = math.hypot(dx, dy)
    check('停止不漂移', drift < 0.03 and abs(dyaw) < 0.05,
          f'2s 漂移 {drift*1000:.1f} mm / {dyaw:.4f} rad')

    print('')
    if fails == 0:
        print('TEST MOTION SUMMARY: 3/3 PASS -> OK')
    else:
        print(f'TEST MOTION SUMMARY: {3-fails}/3 PASS -> FAILED')
    rclpy.shutdown()
    sys.exit(0 if fails == 0 else 1)


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:
        print(f'[FAIL] {e}')
        sys.exit(1)
PY
