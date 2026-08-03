#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_report.py — 生成 SLAM 对比实验 Markdown 报告（阶段 13）

汇总 environment.json / 两算法的 cpu_memory.csv + summary.json +
navigation_trials.csv，生成 comparison_report.md。
结论完全由实测数据得出，不预设优劣。

用法：
    python3 generate_report.py --experiment-dir results/YYYYMMDD_HHMMSS
"""
import argparse
import csv
import json
import sys
from pathlib import Path


def read_csv_stats(path):
    """从 cpu_memory.csv 计算平均/峰值 CPU 与 RSS。"""
    cpu, rss = [], []
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            try:
                cpu.append(float(row['cpu_percent']))
                rss.append(float(row['rss_mb']))
            except (ValueError, KeyError):
                continue
    if not cpu:
        return None
    return {
        'cpu_avg': round(sum(cpu) / len(cpu), 2),
        'cpu_peak': round(max(cpu), 2),
        'rss_avg_mb': round(sum(rss) / len(rss), 2),
        'rss_peak_mb': round(max(rss), 2),
        'samples': len(cpu),
    }


def main():
    parser = argparse.ArgumentParser(description='SLAM 对比实验报告生成')
    parser.add_argument('--experiment-dir', required=True)
    args = parser.parse_args()

    exp = Path(args.experiment_dir)
    md = [f'# SLAM 对比实验报告 — {exp.name}',
          '',
          '> 结论由以下实测数据得出，不预设某算法更优。']

    # environment.json
    env_path = exp / 'environment.json'
    if env_path.exists():
        env = json.loads(env_path.read_text())
        md += ['', '## 实验环境', '',
               f"- 算法版本: {env.get('algorithms', {})}",
               f"- 世界: {env.get('world')}",
               f"- bag: {env.get('bag')}",
               f"- 传感器: {env.get('sensors')}"]

    # 两算法资源与地图
    md += ['', '## 资源占用（回放同一 bag）', '',
           '| 指标 | SLAM Toolbox | Cartographer |',
           '|------|-------------|--------------|']
    rows = {}
    for algo in ('slam_toolbox', 'cartographer'):
        d = exp / algo
        st = read_csv_stats(d / 'cpu_memory.csv') if (d / 'cpu_memory.csv').exists() else None
        summary = json.loads((d / 'summary.json').read_text()) if (d / 'summary.json').exists() else {}
        rows[algo] = {'res': st, 'map': summary}
    for metric in ('cpu_avg', 'cpu_peak', 'rss_avg_mb', 'rss_peak_mb'):
        def fmt(algo):
            r = rows.get(algo, {}).get('res')
            return f"{r[metric]}" if r and metric in r else '—'
        md.append(f'| {metric} | {fmt("slam_toolbox")} | {fmt("cartographer")} |')

    md += ['', '## 地图指标（map_statistics）', '',
           '| 指标 | SLAM Toolbox | Cartographer |',
           '|------|-------------|--------------|']
    for key in ('occupied_ratio', 'free_ratio', 'unknown_ratio',
                'corridor_noise_px', 'north_wall_segments'):
        def mfmt(algo):
            s = rows.get(algo, {}).get('map', {})
            cov = s.get('coverage', {})
            cla = s.get('clarity', {})
            v = cov.get(key) if key in cov else cla.get(key)
            return str(v) if v is not None else '—'
        md.append(f'| {key} | {mfmt("slam_toolbox")} | {mfmt("cartographer")} |')

    # 导航试验
    trials = exp / 'navigation_trials.csv'
    if trials.exists():
        md += ['', '## 导航表现（每地图 5 目标 × 3 次）', '',
               '| 指标 | SLAM Toolbox | Cartographer |',
               '|------|-------------|--------------|']
        data = {}
        with open(trials, newline='') as f:
            for row in csv.DictReader(f):
                data.setdefault(row['map_name'], []).append(row)
        for algo in ('slam_toolbox', 'cartographer'):
            sub = data.get(algo, [])
            ok = sum(1 for r in sub if r['success'] == 'yes')
            times = [float(r['navigation_time_s']) for r in sub
                     if r.get('navigation_time_s')]
            recs = [int(r['recovery_count']) for r in sub
                    if r.get('recovery_count')]
            mins = [float(r['min_scan_range_m']) for r in sub
                    if r.get('min_scan_range_m')]
            rows[algo]['trials'] = {
                'success': f'{ok}/{len(sub)}',
                'avg_time_s': round(sum(times) / len(times), 1) if times else '—',
                'avg_recovery': round(sum(recs) / len(recs), 1) if recs else '—',
                'min_min_scan_m': round(min(mins), 2) if mins else '—',
            }
        for key in ('success', 'avg_time_s', 'avg_recovery', 'min_min_scan_m'):
            def tfmt(algo):
                t = rows.get(algo, {}).get('trials', {})
                return str(t.get(key, '—'))
            md.append(f'| {key} | {tfmt("slam_toolbox")} | {tfmt("cartographer")} |')

    md += ['', '## 结论（依据上述数据）', '',
           '> 结论待按实测数据填写：请比较两算法的成功率、耗时、资源占用与'
           '地图指标后，用数据说话（本模板不预设任何结论）。']

    out = exp / 'comparison_report.md'
    out.write_text('\n'.join(md) + '\n')
    print(f'[generate_report] 已写入 {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
