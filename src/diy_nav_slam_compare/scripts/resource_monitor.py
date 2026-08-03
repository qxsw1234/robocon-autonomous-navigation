#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""resource_monitor.py — 进程 CPU/内存监控（阶段 13）

用 psutil 周期性采样指定进程的 CPU 占用与 RSS 内存，输出 CSV：
    timestamp, cpu_percent, rss_mb

用法：
    python3 resource_monitor.py --pid <PID> --interval 1.0 \
        --duration 900 --output cpu_memory.csv

进程退出或超时后停止；CSV 字段固定；捕获异常。
"""
import argparse
import csv
import time
from pathlib import Path

import psutil


def main():
    parser = argparse.ArgumentParser(description='进程 CPU/内存监控')
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--interval', type=float, default=1.0)
    parser.add_argument('--duration', type=float, default=900.0)
    parser.add_argument('--output', type=str, required=True)
    args = parser.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    t_end = time.monotonic() + args.duration

    with out.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'cpu_percent', 'rss_mb'])
        try:
            proc = psutil.Process(args.pid)
        except psutil.NoSuchProcess:
            print(f'[resource_monitor] 进程 {args.pid} 不存在')
            return 1
        try:
            proc.cpu_percent(None)  # 首采样用于初始化
            while time.monotonic() < t_end:
                try:
                    cpu = proc.cpu_percent(None)
                    rss = proc.memory_info().rss / 1024 / 1024
                except psutil.NoSuchProcess:
                    print(f'[resource_monitor] 进程 {args.pid} 已退出')
                    break
                writer.writerow([f'{time.time():.3f}', f'{cpu:.2f}', f'{rss:.2f}'])
                f.flush()
                time.sleep(max(0.1, args.interval))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f'[resource_monitor] 异常: {e}')
    print(f'[resource_monitor] 已写入 {out}')
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
