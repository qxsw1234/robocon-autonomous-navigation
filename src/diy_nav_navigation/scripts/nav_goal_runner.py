#!/usr/bin/env python3
# ----------------------------------------------------------------------
# nav_goal_runner.py — 自主导航目标序列测试（阶段 9）
# ----------------------------------------------------------------------
# 用 nav2_simple_commander 依次发送 5 个目标（complex_world）：
#   1. (7.5, 0.0)   走廊东端（开阔区）
#   2. (6.5, 4.5)   R2 房间内（U 形障碍旁，导航需绕行）
#   3. (-2.2, 1.5)  窄门口（0.8 m）另一侧 —— R1 内
#   4. (-6.5, -4.5) R3 西南角（遮挡箱体区）
#   5. (0.0, 0.0)   回起点
# 每个目标记录：坐标 / 成功 / 规划时间 / 导航耗时 / 恢复行为次数 /
#               全程最小激光距离（碰撞近似）/ 失败原因 → CSV
#
# 前置：仿真 + localization + navigation 均已启动。
# 用法：
#   python3 ~/ros2_ws/src/diy_nav_navigation/scripts/nav_goal_runner.py \
#       [--output /path/out.csv] [--initial-x 0 --initial-y 0 --initial-yaw 0]
# ----------------------------------------------------------------------
import argparse
import csv
import math
import sys
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import LaserScan

GOALS = [
    ('走廊东端（开阔）', 7.5, 0.0),
    ('R2 房间内（U 形障碍）', 6.5, 4.5),
    ('R1 窄门口另一侧', -2.2, 1.5),
    ('R3 西南角（遮挡区）', -6.5, -4.5),
    ('回起点', 0.0, 0.0),
]

DEFAULT_OUTPUT = '/home/czm/ros2_ws/results/nav_goals_stage9.csv'


def make_pose(frame, x, y, yaw, clock=None):
    p = PoseStamped()
    p.header.frame_id = frame
    # 关键：必须用仿真时钟打时间戳（节点 use_sim_time: true）。
    # 若用墙钟，AMCL 拒绝初始位姿、bt_navigator 因"目标时间戳超出 TF 缓存"
    # 而无法处理目标（此前 0/5 失败链的一部分）。
    p.header.stamp = (clock or rclpy.clock.Clock()).now().to_msg()
    p.pose.position.x = x
    p.pose.position.y = y
    p.pose.orientation.z = math.sin(yaw / 2.0)
    p.pose.orientation.w = math.cos(yaw / 2.0)
    return p


class ScanMonitor:
    """订阅 /scan，记录全程最小距离（碰撞近似指标）。
    注意：必须用 BEST_EFFORT——/scan 由 scan_filter 以传感器 QoS 发布，
    默认 RELIABLE 订阅会被 DDS 拒绝（QoS 不兼容），收不到任何数据。"""

    def __init__(self):
        self.node = rclpy.create_node('scan_monitor')
        self.min_range = 99.0
        self.min_during_goal = 99.0
        q = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.node.create_subscription(LaserScan, '/scan', self._cb, q)

    def _cb(self, msg):
        r = min(msg.ranges)
        if r < self.min_range:
            self.min_range = r
        if r < self.min_during_goal:
            self.min_during_goal = r

    def start_goal(self):
        self.min_during_goal = 99.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=DEFAULT_OUTPUT)
    parser.add_argument('--initial-x', type=float, default=0.0)
    parser.add_argument('--initial-y', type=float, default=0.0)
    parser.add_argument('--initial-yaw', type=float, default=0.0)
    args = parser.parse_args()

    rclpy.init()
    nav = BasicNavigator()
    monitor = ScanMonitor()
    # 全部节点跟随仿真时钟（/clock），保证时间戳与 Nav2/AMCL 一致
    from rclpy.parameter import Parameter
    nav.set_parameters([Parameter('use_sim_time', value=True)])
    monitor.node.set_parameters([Parameter('use_sim_time', value=True)])

    # ---- 1. 设置初始位姿（规避：无 /initialpose 时 bt_navigator 卡在
    #      "Invalid frame ID map"）----
    nav.setInitialPose(make_pose('map', args.initial_x, args.initial_y, args.initial_yaw,
                                 clock=nav.get_clock()))
    print('[INFO] 初始位姿已发布，等待 Nav2 激活...')
    nav.waitUntilNav2Active()  # 等 lifecycle 全 active + AMCL 定位就绪
    print('[INFO] Nav2 已激活，开始目标序列')

    rows = []
    for i, (name, gx, gy) in enumerate(GOALS, 1):
        monitor.start_goal()
        goal = make_pose('map', gx, gy, 0.0, clock=nav.get_clock())
        print(f'\n[{i}/{len(GOALS)}] {name}: ({gx}, {gy})')
        nav.goToPose(goal)

        t_start = time.time()
        plan_time = None
        nav_time = None
        recoveries = 0
        feedback_log = []
        while not nav.isTaskComplete():
            feedback = nav.getFeedback()
            if feedback is not None:
                if plan_time is None and feedback.number_of_recoveries > 0:
                    pass
                recoveries = max(recoveries, int(feedback.number_of_recoveries))
            rclpy.spin_once(monitor.node, timeout_sec=0.05)
            time.sleep(0.05)

        nav_time = time.time() - t_start
        result = nav.getResult()

        success = result == TaskResult.SUCCEEDED
        if result == TaskResult.SUCCEEDED:
            reason = ''
        elif result == TaskResult.FAILED:
            reason = 'FAILED'
        elif result == TaskResult.CANCELED:
            reason = 'CANCELED'
        else:
            reason = f'UNKNOWN({result})'

        print(f'    结果: {"成功" if success else "失败"}  耗时 {nav_time:.1f} s  '
              f'恢复 {recoveries} 次  最小激光 {monitor.min_during_goal:.2f} m  '
              f'原因: {reason or "-"}')

        rows.append({
            'goal_index': i,
            'goal_name': name,
            'goal_x': gx,
            'goal_y': gy,
            'success': 'yes' if success else 'no',
            'planning_time_s': '' if plan_time is None else f'{plan_time:.2f}',
            'navigation_time_s': f'{nav_time:.2f}',
            'recovery_count': recoveries,
            'min_scan_range_m': f'{monitor.min_during_goal:.3f}',
            'failure_reason': reason,
        })

    # ---- 2. 写 CSV ----
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    ok = sum(1 for r in rows if r['success'] == 'yes')
    print(f'\nSUMMARY: {ok}/{len(rows)} 成功 → CSV 已写入 {args.output}')
    rclpy.shutdown()
    sys.exit(0 if ok == len(rows) else 1)


if __name__ == '__main__':
    main()
