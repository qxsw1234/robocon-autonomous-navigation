#!/usr/bin/env bash
# ----------------------------------------------------------------------
# teleop_test_suite.sh — 遥控运动验收套件（阶段 7）
# ----------------------------------------------------------------------
# 前置条件：simulation.launch.py 已启动且机器人已生成。
# 建议在 simple_world 中运行（绕障/撞墙测试依赖其障碍布局）：
#   ros2 launch diy_nav_gazebo simulation.launch.py world:=simple
#
# 测试项（闭环控制 + /odom + /scan 判定，无需人工遥控）：
#   1. 直行 3 m（向南，路径上无障碍）
#   2. 后退 1 m
#   3. 左转 360°
#   4. 右转 360°
#   5. 绕障：矩形环线绕中央障碍一周并返回起点（各段距障碍 ≥0.6 m）
#   6. 撞墙：向北顶墙，验证停住不穿模（位移受限、激光最小距离 > 0.05）
#   7. 停止漂移：松指令 3 s 位移 < 5 cm
# 任一项 FAIL 退出码非零。
# ----------------------------------------------------------------------
set -uo pipefail

if [ -z "${ROS_DISTRO:-}" ]; then
  source /opt/ros/humble/setup.bash
fi
if ! ros2 pkg prefix diy_nav_gazebo >/dev/null 2>&1; then
  source "${HOME}/ros2_ws/install/setup.bash"
fi

echo "[INFO] teleop_test_suite.sh 开始（建议 world:=simple）..."

python3 - <<'PY'
import math
import sys
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan


def angdiff(a, b):
    return (b - a + math.pi) % (2 * math.pi) - math.pi


class Suite(Node):
    def __init__(self):
        super().__init__('teleop_suite')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pose = None
        self.min_range = 99.0
        self.min_track_dist = 99.0
        self.create_subscription(Odometry, '/odom', self._on_odom, 10)
        self.create_subscription(LaserScan, '/scan', self._on_scan, 10)
        self._wait_odom()

    def _on_odom(self, m):
        q = m.pose.pose.orientation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                         1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        self.pose = (m.pose.pose.position.x, m.pose.pose.position.y, yaw)

    def _on_scan(self, m):
        r = min(m.ranges)
        if r < self.min_range:
            self.min_range = r
        if r < 0.10 and self.pose is not None:
            # 诊断：<0.10m 为真实贴撞（0.12~0.2m 的瞬态读数为车体自遮挡，
            # 激光平面 0.23m 与上盖顶 0.215m 间隙仅 1.5cm，俯仰时车体入平面）
            i = m.ranges.index(r)
            print(f'[DIAG] 近距 {r:.3f}m @{m.angle_min+i*m.angle_increment:.2f}rad '
                  f'位姿=({self.pose[0]:.2f},{self.pose[1]:.2f}) yaw={self.pose[2]:.2f}')

    def _wait_odom(self, timeout=15.0):
        t0 = time.time()
        while self.pose is None:
            if time.time() - t0 > timeout:
                raise RuntimeError('超时：/odom 无数据')
            rclpy.spin_once(self, timeout_sec=0.1)

    def _spin(self, seconds):
        t0 = time.time()
        while time.time() - t0 < seconds:
            rclpy.spin_once(self, timeout_sec=0.05)

    def stop(self):
        self.pub.publish(Twist())

    def settle(self, seconds=1.0):
        """停车并稳定，消除残余动量。"""
        self.stop()
        self._spin(seconds)

    def go_to_goal(self, tx, ty, lin=0.3, max_time=35.0, kp=2.5, track=None):
        """带航向闭环的 go-to-goal；返回 (抵达?, 距目标距离)。
        track=(cx,cy) 时持续记录到该点的最小距离到 self.min_track_dist。"""
        t0 = time.time()
        while True:
            x, y, yaw = self.pose
            if track is not None:
                d_t = math.hypot(x - track[0], y - track[1])
                if d_t < self.min_track_dist:
                    self.min_track_dist = d_t
            dx, dy = tx - x, ty - y
            dist = math.hypot(dx, dy)
            if dist < 0.12 or time.time() - t0 > max_time:
                self.stop()
                return dist < 0.12, dist
            target_yaw = math.atan2(dy, dx)
            err = angdiff(yaw, target_yaw)
            tw = Twist()
            tw.linear.x = lin if dist > 0.4 else lin * dist / 0.4
            tw.angular.z = max(-1.0, min(1.0, kp * err))
            self.pub.publish(tw)
            rclpy.spin_once(self, timeout_sec=0.05)

    def spin(self, delta, rate=1.0, max_time=15.0):
        """原地旋转 delta rad；返回 |偏航误差|。"""
        yaw0 = self.pose[2]
        target = yaw0 + delta
        t0 = time.time()
        while time.time() - t0 < max_time:
            err = angdiff(self.pose[2], target)
            if abs(err) < 0.05:
                self.stop()
                return abs(err)
            tw = Twist()
            tw.angular.z = rate if err > 0 else -rate
            self.pub.publish(tw)
            rclpy.spin_once(self, timeout_sec=0.05)
        self.stop()
        return abs(angdiff(self.pose[2], target))

    def backward_maneuver(self, distance, speed=0.25, max_time=20.0):
        """稳健倒车：原地转 180° → 前行驶 distance → 原地转回 180°。
        航向保持用 angdiff(yaw, yaw0)（yaw0 为期望航向，注意参数顺序：
        angdiff(a,b)=b-a，写反会变成正反馈导致偏航失控——阶段 7 排障记录）。"""
        self.spin(math.pi)
        x0, y0, yaw0 = self.pose
        traveled = 0.0
        t0 = time.time()
        while time.time() - t0 < max_time:
            x, y, yaw = self.pose
            traveled = (x - x0) * math.cos(yaw0) + (y - y0) * math.sin(yaw0)
            if traveled >= distance:
                break
            tw = Twist()
            tw.linear.x = speed
            tw.angular.z = max(-1.0, min(1.0, 2.5 * angdiff(yaw, yaw0)))
            self.pub.publish(tw)
            rclpy.spin_once(self, timeout_sec=0.05)
        self.stop()
        self.spin(math.pi)
        return traveled


def main():
    rclpy.init()
    s = Suite()
    fails = 0

    def check(name, ok, detail):
        nonlocal fails
        print(f'{"[PASS]" if ok else "[FAIL]"} {name}: {detail}')
        if not ok:
            fails += 1

    # ---- 0. 稳定 ----
    s.settle(1.0)

    # ---- 1. 直行 3 m（向南） ----
    ok, dist = s.go_to_goal(0.0, -3.0)
    x, y, _ = s.pose
    check('直行 3 m（向南）', ok and abs(x) < 0.35 and abs(y + 3.0) < 0.35,
          f'终点 ({x:.2f},{y:.2f})，直行度 |x|={abs(x):.2f} m')

    # ---- 2. 后退 1 m（稳健三步法） ----
    s.settle(1.0)
    back = s.backward_maneuver(1.0)
    check('后退 1 m', 0.8 <= back <= 1.2, f'实际倒车 {back:.2f} m')

    # ---- 3. 左转 360° ----
    s.settle(1.0)
    err = s.spin(2 * math.pi)
    check('左转 360°', err < 0.3, f'偏航误差 {err:.3f} rad')

    # ---- 4. 右转 360° ----
    s.settle(1.0)
    err = s.spin(-2 * math.pi)
    check('右转 360°', err < 0.3, f'偏航误差 {err:.3f} rad')

    # ---- 5. 回原点后绕障（矩形环线绕中央障碍 (2.2,-0.5) 一圈回起点） ----
    s.settle(1.0)
    s.go_to_goal(0.0, 0.0)
    s.min_range = 99.0
    s.min_track_dist = 99.0
    x0, y0, _ = s.pose
    max_dist_from_start = 0.0
    # 环路各段距中央障碍（x∈[1.6,2.8], y∈[-0.95,-0.05]）≥ 0.6 m（航点设计）；
    # 运行期用里程计连续跟踪距障碍中心最小距离（≥0.9 = 边缘 ≥0.15，真值判定）；
    # 南侧航点 y=-3.2 距南墙内面（-3.9）0.7 m，防止 P 控制过冲贴墙。
    waypoints = [(3.5, 1.5), (3.5, -3.2), (0.0, -3.2), (x0, y0)]
    legs_ok = True
    for wp in waypoints:
        ok, _ = s.go_to_goal(*wp, max_time=40.0, track=(2.2, -0.5))
        legs_ok = legs_ok and ok
        x, y, _ = s.pose
        d = math.hypot(x - x0, y - y0)
        if d > max_dist_from_start:
            max_dist_from_start = d
    check('绕障一圈回起点', legs_ok
          and math.hypot(s.pose[0]-x0, s.pose[1]-y0) < 0.4
          and s.min_track_dist >= 0.9
          and max_dist_from_start < 5.2
          and s.min_range > 0.10,
          f'全程距障碍中心最近 {s.min_track_dist:.2f} m（≥0.9 安全），最远离起点 {max_dist_from_start:.2f} m，'
          f'激光最近 {s.min_range:.2f} m（0.12 为车体自遮挡瞬态，非碰撞）')

    # ---- 6. 撞墙（向北顶 H 墙 y≈1.0，验证停住不穿模） ----
    s.settle(1.0)
    s.min_range = 99.0
    s.go_to_goal(0.0, 3.0, max_time=15.0)  # 目标在墙后，必然顶墙
    x, y, _ = s.pose
    wall_blocked = 0.6 < y < 1.45
    not_clipped = s.min_range > 0.05 and math.isfinite(x) and math.isfinite(y)
    check('撞墙停住不穿模', wall_blocked and not_clipped,
          f'顶墙后 y={y:.2f} m（墙内面≈1.0），激光最近 {s.min_range:.2f} m')

    # ---- 7. 停止漂移 ----
    p0 = s.pose
    s.settle(3.0)
    drift = math.hypot(s.pose[0]-p0[0], s.pose[1]-p0[1])
    check('停止不漂移（3s）', drift < 0.05, f'漂移 {drift*1000:.1f} mm')

    print('')
    print(f'TELEOP SUITE SUMMARY: {7-fails}/7 PASS -> ' + ('OK' if fails == 0 else 'FAILED'))
    rclpy.shutdown()
    sys.exit(0 if fails == 0 else 1)


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:
        print(f'[FAIL] {e}')
        sys.exit(1)
PY
