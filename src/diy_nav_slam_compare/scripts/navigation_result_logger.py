#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""navigation_result_logger.py — 导航试验结果汇总（阶段 13）

把 nav_goal_runner 的 CSV（每轮 5 目标）合并为导航试验总表：
    map_name, run, goal_index, goal_name, success, navigation_time_s,
    recovery_count, min_scan_range_m

输出：results/时间戳/navigation_trials.csv

用法：
    python3 navigation_result_logger.py \
        --slam-csv a.csv b.csv --carto-csv c.csv d.csv \
        --output navigation_trials.csv
"""
import argparse
import csv
import sys
from pathlib import Path


def read_runs(csv_paths, map_name):
    rows = []
    for run_idx, p in enumerate(csv_paths, 1):
        try:
            with open(p, newline='') as f:
                reader = csv.DictReader(f)
                for i, r in enumerate(reader, 1):
                    rows.append({
                        'map_name': map_name,
                        'run': run_idx,
                        'goal_index': i,
                        'goal_name': r.get('goal_name', ''),
                        'success': r.get('success', ''),
                        'navigation_time_s': r.get('navigation_time_s', ''),
                        'recovery_count': r.get('recovery_count', ''),
                        'min_scan_range_m': r.get('min_scan_range_m', ''),
                        'failure_reason': r.get('failure_reason', ''),
                    })
        except Exception as e:
            print(f'[navigation_result_logger] 读取 {p} 失败: {e}',
                  file=sys.stderr)
    return rows


def main():
    parser = argparse.ArgumentParser(description='导航试验结果汇总')
    parser.add_argument('--slam-csv', nargs='+', default=[])
    parser.add_argument('--carto-csv', nargs='+', default=[])
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    rows = (read_runs(args.slam_csv, 'slam_toolbox') +
            read_runs(args.carto_csv, 'cartographer'))
    if not rows:
        print('[navigation_result_logger] 无任何数据', file=sys.stderr)
        return 1

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # 汇总统计
    for map_name in ('slam_toolbox', 'cartographer'):
        sub = [r for r in rows if r['map_name'] == map_name]
        if not sub:
            continue
        ok = sum(1 for r in sub if r['success'] == 'yes')
        times = [float(r['navigation_time_s']) for r in sub
                 if r['navigation_time_s']]
        print(f'[navigation_result_logger] {map_name}: '
              f'{ok}/{len(sub)} 成功, 平均耗时 '
              f'{sum(times)/len(times):.1f}s' if times else
              f'[navigation_result_logger] {map_name}: {ok}/{len(sub)} 成功')
    print(f'[navigation_result_logger] 已写入 {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
