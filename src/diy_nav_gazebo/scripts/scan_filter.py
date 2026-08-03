#!/usr/bin/env python3
# ----------------------------------------------------------------------
# scan_filter.py — 激光扫描过滤器（车体自遮挡抑制）
# ----------------------------------------------------------------------
# 问题：激光平面（0.23 m）与车体顶面间隙小，运动俯仰时上盖/底盘边缘
# 进入扫描平面，产生 0.12~0.25 m 的车体自遮挡读数（0.38×0.28 上盖阶段
# 甚至恒定出现）。这些读数会：① 被 SLAM 栅格化进地图（窄门口被机器人
# 自身"填死"）；② 让 DWB 局部规划器把车体当成紧贴障碍；③ 干扰 AMCL 匹配。
#
# 方案：订阅 /scan_raw（Gazebo 传感器原始输出），把 < 0.16 m 的读数置为
# 无效（inf），重新发布 /scan——所有下游（SLAM/AMCL/代价地图/RViz）自动
# 获得干净扫描。阈值 0.16：当前上盖边缘 0.10~0.12 m（盲区内）、底盘
# 半宽 0.16 m（>0.16，仅在 >8.9° 极端俯仰时进入，瞬态可接受）；
# 真实障碍（走廊墙 ≥0.35 m、窄门口墙 0.155~0.2 m 由接近段扫描补足）不受影响。
#
# 前置：仿真已启动。用法：由 simulation.launch.py 自动拉起。
# ----------------------------------------------------------------------
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import LaserScan

MIN_VALID_RANGE = 0.23  # 低于此值的读数视为车体自遮挡
# 阈值说明（0.16 → 0.23 升级，根因：车体在激光平面的最大外缘为
# 底盘前端 0.225 m / 侧面 0.16 m，0.16 阈值只滤掉侧面，前端读数
# (0.16~0.225 m) 仍被 SLAM 烘焙进地图，在建图停留点留下 0.4×0.4 的
# "机器人本体"占用块（corridor 内 x≈-5.0 与 x≈4.95 两处，已人工清除）。
# 0.23 阈值：车体全部读数 (<0.225) 被滤除；真实障碍最近距离——
# 窄门口 (0.8 m) 门框正面 0.24 m、走廊墙 ≥0.56 m——全部不受影响。

# QoS 关键：Gazebo 传感器与 Nav2（AMCL / costmap 的 ObservationBuffer）
# 均以 BEST_EFFORT 订阅 /scan。若此处用默认 RELIABLE 发布，DDS 认为二者
# QoS 不兼容 → AMCL/costmap 收不到任何扫描（表现为定位不更新、导航"失明"
# 撞墙）。BEST_EFFORT 发布对 RELIABLE 订阅者（slam_toolbox/RViz）仍兼容。
# 双发布：/scan（BEST_EFFORT → Nav2/AMCL/costmap）+ /scan_slam（RELIABLE
# → slam_toolbox / cartographer，其订阅若为 RELIABLE 则收不到 BE 数据）。
SENSOR_QOS = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
RELIABLE_QOS = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)


class ScanFilter(Node):
    def __init__(self):
        super().__init__('scan_filter')
        self.pub = self.create_publisher(LaserScan, '/scan', SENSOR_QOS)
        self.pub_slam = self.create_publisher(LaserScan, '/scan_slam', RELIABLE_QOS)
        self.sub = self.create_subscription(
            LaserScan, '/scan_raw', self._cb, SENSOR_QOS)

    def _cb(self, msg):
        ranges = list(msg.ranges)
        for i, r in enumerate(ranges):
            if not math.isfinite(r) or r < MIN_VALID_RANGE:
                ranges[i] = float('inf')
        msg.ranges = ranges
        msg.range_min = MIN_VALID_RANGE
        self.pub.publish(msg)
        self.pub_slam.publish(msg)


def main():
    rclpy.init()
    node = ScanFilter()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
