"""diy_nav_slam_compare.cli

骨架阶段占位 CLI。仅打印包名、版本和当前实现状态，
后续阶段将替换为真正的 SLAM 比较入口（录制/回放/指标计算）。
"""

from __future__ import annotations


def main() -> int:
    """占位入口，返回 0 表示 CLI 可正常调用。"""
    print('diy_nav_slam_compare v0.1.0 — skeleton stage')
    print('CLI placeholder; benchmark commands will be added in later stages.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
