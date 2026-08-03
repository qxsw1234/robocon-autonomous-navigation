#!/usr/bin/env python3
# ----------------------------------------------------------------------
# mapping_tour.py — SLAM 建图自动巡航（阶段 8）
# ----------------------------------------------------------------------
# 按 complex_world（16×12 m）几何预设航点，用 /cmd_vel 闭环行驶：
#   起点(0,0) → 走廊东段 → R2（绕 U 形障碍）→ 走廊 → R4（绕 L 形障碍）
#   → 走廊西段 → R1（0.8 m 窄门口，慢行）→ R3（绕遮挡箱体）→ 回起点闭环
# 线速 0.25 m/s（窄处 0.15），角速上限 0.6 rad/s，转弯自然降速——
# 保证扫描重叠率，利于 SLAM 帧间匹配与回环闭合。
#
# 用法（先启动仿真 + slam_toolbox）：
#   python3 ~/ros2_ws/src/diy_nav_navigation/scripts/mapping_tour.py
# 结束后地图已更新完毕，可保存：
#   ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/src/diy_nav_navigation/maps/complex_slam_toolbox
# ----------------------------------------------------------------------
import math
import sys
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from nav_msgs.msg import OccupancyGrid


def angdiff(a, b):
    return (b - a + math.pi) % (2 * math.pi) - math.pi


# 航点表：(x, y, slow?)  —— slow=True 时线速 0.15 m/s（0.8 m 窄门口）
ROUTE = [
    # 起点 → 走廊东段
    (0.0, 0.4, False),
    (4.0, 0.4, False),
    # 进 R2（门口 x∈[1.5,2.7]）
    (2.1, 0.4, False),
    (2.1, 1.5, False),
    # R2 内绕 U 形障碍（x∈[4.6,6.2], y∈[3.2,5.2]）
    (2.1, 3.0, False),
    (3.2, 3.0, False),
    (3.2, 5.5, False),
    (7.0, 5.5, False),
    (7.0, 2.5, False),
    (4.5, 2.5, False),
    # 出 R2 回走廊
    (2.1, 1.5, False),
    (2.1, 0.4, False),
    # 进 R4（门口 x∈[3.5,4.5]）
    (4.0, 0.4, False),
    (4.0, -0.4, False),
    (4.0, -1.5, False),
    # R4 内绕 L 形障碍（v:x∈[5.1,5.3] y∈[-4.9,-2.9]; h:x∈[5.2,7.4] y∈[-5.0,-4.8]）
    # 注意：v 墙纵向贯穿 y∈[-4.9,-2.9]，任何在 y∈[-4.9,-2.9] 的横向航段都会穿墙，
    # 因此必须先南绕到 y=-5.5（排障记录：初版航段 (4.5,-4.5)→(6.5,-4.5) 撞墙）
    (4.0, -3.0, False),
    (4.5, -3.0, False),
    (4.5, -5.5, False),
    (6.5, -5.5, False),
    (3.0, -5.5, False),
    (3.0, -3.0, False),
    (5.0, -1.8, False),      # 覆盖 R4 东北角与箱体区
    # 出 R4 回走廊
    (4.0, -1.5, False),
    (4.0, -0.4, False),
    # 走廊西段
    (4.0, 0.4, False),
    (0.0, 0.4, False),
    (-7.5, 0.4, False),
    # 进 R1（0.8 m 窄门口 x∈[-2.6,-1.8]，慢行）
    (-2.2, 0.4, True),
    (-2.2, 1.5, True),
    # R1 内部（绕箱体）
    (-2.2, 3.0, False),
    (-5.5, 3.0, False),
    (-5.5, 5.5, False),
    (-2.0, 5.5, False),
    (-2.0, 3.0, False),
    # 出 R1（窄门口慢行）
    (-2.2, 1.5, True),
    (-2.2, 0.4, True),
    # 进 R3（门口 x∈[-1,0]）
    (-0.5, -0.4, False),
    (-0.5, -1.5, False),
    # R3 内绕遮挡箱体（x∈[-5.5,-3.5], y∈[-4.1,-2.9]）与箱体 box_r3（x∈[-1.85,-1.15],
    # y∈[-2.85,-2.15]）：两障碍之间 x∈[-3.5,-1.85] 是 1.65 m 宽缝隙（唯一东西通道）。
    # 初版航段 (-0.5,-3.0)→(-2.8,-3.0) 擦撞 box_r3 南缘（y 间距 0.15 < 半宽 0.245），
    # (-0.5,-2.6) 横穿 box_r3 也撞——排障记录：必须 box_r3 北侧西行→缝隙南下→
    # 遮挡箱南侧→缝隙北上→box_r3 南侧东行返回。
    (-0.5, -1.5, False),
    (-0.5, -1.7, False),
    (-2.5, -1.7, False),
    (-2.5, -4.5, False),
    (-6.5, -4.5, False),
    (-6.5, -5.5, False),
    (-2.8, -5.5, False),
    (-2.8, -3.3, False),
    (-0.5, -3.3, False),
    # 出 R3 回走廊 → 回起点闭环
    (-0.5, -1.5, False),
    (-0.5, -0.4, False),
    (0.0, 0.4, False),
]


class Tour(Node):
    def __init__(self):
        super().__init__('mapping_tour')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pose = None
        self.map_received = False
        self.create_subscription(Odometry, '/odom', self._on_odom, 10)
        self.create_subscription(OccupancyGrid, '/map', self._on_map, 10)
        self._wait_ready()

    def _on_odom(self, m):
        q = m.pose.pose.orientation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                         1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        self.pose = (m.pose.pose.position.x, m.pose.pose.position.y, yaw)

    def _on_map(self, _):
        self.map_received = True

    def _wait_ready(self, timeout=30.0):
        """等待：/odom 有数据 + SLAM 已发布 /map（map→odom TF 就绪的间接证据）。"""
        t0 = time.time()
        while time.time() - t0 < timeout:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.pose is not None and self.map_received:
                self.get_logger().info('SLAM 已就绪（/map 到达），开始巡航')
                return
        raise RuntimeError('超时：/odom 或 /map 无数据（仿真与 slam_toolbox 是否已启动？）')

    def go_to_goal(self, tx, ty, slow=False, kp=2.0):
        lin = 0.15 if slow else 0.25
        t0 = time.time()
        while True:
            x, y, yaw = self.pose
            dx, dy = tx - x, ty - y
            dist = math.hypot(dx, dy)
            if dist < 0.12 or time.time() - t0 > 60.0:
                self.stop()
                return dist < 0.12, dist
            target_yaw = math.atan2(dy, dx)
            err = angdiff(yaw, target_yaw)
            tw = Twist()
            # 转弯降速：航向误差大时减速，保证扫描重叠
            speed = lin * max(0.35, 1.0 - abs(err) / 1.2)
            tw.linear.x = speed if dist > 0.3 else speed * dist / 0.3
            tw.angular.z = max(-0.6, min(0.6, kp * err))
            self.pub.publish(tw)
            rclpy.spin_once(self, timeout_sec=0.05)

    def stop(self):
        self.pub.publish(Twist())


def main():
    rclpy.init()
    tour = Tour()
    total_wp = len(ROUTE)
    failed = 0
    t_start = time.time()
    for i, (x, y, slow) in enumerate(ROUTE, 1):
        ok, dist = tour.go_to_goal(x, y, slow=slow)
        tag = 'PASS' if ok else 'FAIL'
        if not ok:
            failed += 1
        tour.get_logger().info(
            f'[{i}/{total_wp}] 航点 ({x:.1f},{y:.1f}){" [慢]" if slow else ""}: '
            f'{tag}（剩余 {dist:.2f} m）')
        # 航点间稍作停留，让 SLAM 消化扫描
        tour.stop()
        time.sleep(1.0)
        rclpy.spin_once(tour, timeout_sec=0.1)

    tour.stop()
    elapsed = time.time() - t_start
    print('')
    print(f'TOUR SUMMARY: {total_wp - failed}/{total_wp} 航点完成，用时 {elapsed:.0f} s')
    print('建议等待 10 s（map_update_interval=2 s）后再保存地图。')
    print('保存命令: ros2 run nav2_map_server map_saver_cli '
          '-f ~/ros2_ws/src/diy_nav_navigation/maps/complex_slam_toolbox')
    rclpy.shutdown()
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:
        print(f'[FAIL] {e}')
        sys.exit(1)
