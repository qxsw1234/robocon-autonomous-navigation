#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""save_map.py — 从 /map 话题保存占用栅格地图（PGM + YAML）。

背景：map_saver_cli 在本环境偶发 "Failed to spin map subscription" 失败，
且保存结果可能滞后于实时地图。本工具用 transient_local QoS 直接订阅
/map（与 slam_toolbox 的发布 QoS 匹配，必能拿到最新 latch 地图），
立即落盘，输出格式与 map_saver 完全兼容（占用 0、自由 205、线性过渡）。

用法：
    ros2 run diy_nav_navigation save_map  <输出前缀，默认 /tmp/robot_map>
    # 例：存到包内 maps 目录
    ros2 run diy_nav_navigation save_map  ~/ros2_ws/src/diy_nav_navigation/maps/complex_slam_toolbox
"""
import sys
import time

import rclpy
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from nav_msgs.msg import OccupancyGrid

OCCUPIED_PGM = 0      # 占用 → PGM 0（黑）
FREE_PGM = 205        # 自由 → PGM 205（白）
NEGATE = 0            # 0 = 值越大越自由


def occupancy_to_pgm(value: int) -> int:
    """占用概率(0-100) → PGM 灰度(0-255)，与 nav2 map_saver 相同的线性映射。"""
    if value < 0:                      # 未知
        return 205
    p = value / 100.0
    if p >= 0.65:                      # occupied_thresh
        return OCCUPIED_PGM
    if p <= 0.25:                      # free_thresh
        return FREE_PGM
    return int((1.0 - p) * 205.0)      # 0.25 < p < 0.65 线性过渡


def save_map(msg, prefix: str):
    pgm_path = prefix + '.pgm'
    yaml_path = prefix + '.yaml'
    w, h = msg.info.width, msg.info.height
    pgm = bytearray([FREE_PGM]) * (w * h)      # 默认自由
    for i, v in enumerate(msg.data):
        pgm[i] = occupancy_to_pgm(v)
    with open(pgm_path, 'wb') as f:
        f.write(f'P5\n# CREATOR: save_map.py\n{w} {h}\n255\n'.encode())
        f.write(bytes(pgm))
    yaml = (
        f'image: {prefix.split("/")[-1]}.pgm\n'
        f'mode: trinary\n'
        f'resolution: {msg.info.resolution}\n'
        f'origin: [{msg.info.origin.position.x}, {msg.info.origin.position.y}, {msg.info.origin.position.z}]\n'
        f'negate: {NEGATE}\n'
        f'occupied_thresh: 0.65\n'
        f'free_thresh: 0.25\n'
    )
    with open(yaml_path, 'w') as f:
        f.write(yaml)
    return pgm_path, yaml_path


def main():
    rclpy.init()
    node = rclpy.create_node('map_saver_py')
    prefix = sys.argv[1] if len(sys.argv) > 1 else '/tmp/robot_map'
    q = QoSProfile(depth=1,
                   durability=DurabilityPolicy.TRANSIENT_LOCAL,
                   reliability=ReliabilityPolicy.RELIABLE)
    got = []
    node.create_subscription(OccupancyGrid, '/map',
                             lambda m: got.append(m), qos_profile=q)
    deadline = time.monotonic() + 10.0
    while rclpy.ok() and not got and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.2)
    if not got:
        print(f'[save_map] 错误: 10 秒内未收到 /map 消息', file=sys.stderr)
        return 1
    msg = got[0]
    pgm_path, yaml_path = save_map(msg, prefix)
    n_occ = sum(1 for v in msg.data if v > 60)
    n_free = sum(1 for v in msg.data if v < 25)
    print(f'[save_map] 已保存 {pgm_path}')
    print(f'[save_map] 地图 {msg.info.width}x{msg.info.height} 分辨率 {msg.info.resolution}')
    print(f'[save_map] 时间戳 t={msg.header.stamp.sec}.{msg.header.stamp.nanosec // 1000000}  '
          f'占用 {n_occ} 格 / 自由 {n_free} 格')
    node.destroy_node()
    rclpy.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
