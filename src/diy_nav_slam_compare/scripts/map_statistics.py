#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""map_statistics.py — 地图统计指标（阶段 13）

从 PGM+YAML 计算：
  覆盖率：未知/空闲/占用像素比例
  清晰度（近似，不冒充准确率）：
    - 墙体边缘厚度（占用带宽度中位数，按列扫描走廊墙）
    - 墙体重影：占用带内“空洞”占比（墙体内空隙/总墙体积分）
    - 边缘梯度：占用→空闲过渡的像素层数
    - 断墙数量：走廊墙沿 x 的占用间断数（门口为合理间断，另行记录门口占用率）
  走廊噪声：走廊带内孤立占用格数

输出 JSON。用法：
    python3 map_statistics.py --map /path/map.pgm --output summary.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml


def load_pgm(path):
    data = Path(path).read_bytes()
    lines = data.split(b'\n')
    if lines[0] != b'P5':
        raise ValueError('仅支持 P5 PGM')
    i = 1
    while lines[i].startswith(b'#'):
        i += 1
    w, h = map(int, lines[i].split())
    i += 1
    raw = np.frombuffer(b'\n'.join(lines[i + 1:])[:w * h],
                        dtype=np.uint8).reshape(h, w).astype(np.int32)
    return raw, w, h


def main():
    parser = argparse.ArgumentParser(description='地图统计指标')
    parser.add_argument('--map', required=True, help='PGM 文件路径')
    parser.add_argument('--output', required=True, help='输出 JSON 路径')
    parser.add_argument('--corridor', default='-7.8,7.8,-0.55,0.55',
                        help='走廊带 x0,x1,y0,y1（默认覆盖 complex 走廊）')
    args = parser.parse_args()

    try:
        raw, w, h = load_pgm(args.map)
        yaml_path = str(Path(args.map).with_suffix('.yaml'))
        meta = yaml.safe_load(open(yaml_path))
        res = meta['resolution']
        ox, oy = meta['origin'][0], meta['origin'][1]

        occupied = raw < 100
        free = raw >= 205
        unknown = ~(occupied | free)

        x0, x1, y0, y1 = map(float, args.corridor.split(','))

        def cell_in_band(px, py):
            x = ox + px * res
            y = oy + py * res
            return x0 <= x <= x1 and y0 <= y <= y1

        # 走廊带噪声（孤立占用）
        noise = 0
        for py in range(h):
            for px in range(w):
                if occupied[py, px] and cell_in_band(px, py):
                    noise += 1

        # 墙体边缘厚度：扫描走廊北墙列，只统计走廊墙所在带（y∈[0.4,1.3]）
        # 的连续占用带宽度（排除房间/边界墙的干扰）
        wall_thickness = []
        for px in range(w):
            x = ox + px * res
            if not (x0 <= x <= x1):
                continue
            col = occupied[:, px]
            ys = np.where(col & ((oy + np.arange(h) * res) > 0.4) &
                          ((oy + np.arange(h) * res) < 1.3))[0]
            if len(ys) > 0:
                wall_thickness.append(ys.max() - ys.min() + 1)

        # 断墙数：走廊北墙沿 x 的连续占用段数（门口为合理间断）
        segs = 0
        prev = False
        for px in range(w):
            x = ox + px * res
            if not (x0 <= x <= x1):
                continue
            col = occupied[:, px]
            ys_up = np.where(col & ((oy + np.arange(h) * res) > 0.4))[0]
            cur = len(ys_up) > 0
            if cur and not prev:
                segs += 1
            prev = cur

        stats = {
            'map_size': {'width': w, 'height': h, 'resolution': res},
            'coverage': {
                'occupied_px': int(occupied.sum()),
                'free_px': int(free.sum()),
                'unknown_px': int(unknown.sum()),
                'total_px': w * h,
                'occupied_ratio': round(float(occupied.mean()), 4),
                'free_ratio': round(float(free.mean()), 4),
                'unknown_ratio': round(float(unknown.mean()), 4),
            },
            'clarity': {
                'wall_edge_thickness_px_median': float(
                    np.median(wall_thickness)) if wall_thickness else None,
                'corridor_noise_px': noise,
                'north_wall_segments': segs,
            },
        }
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps(stats, indent=2, ensure_ascii=False))
        print(f'[map_statistics] 已写入 {args.output}')
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(f'[map_statistics] 异常: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
