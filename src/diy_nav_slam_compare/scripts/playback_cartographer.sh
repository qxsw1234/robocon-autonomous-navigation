#!/usr/bin/env bash
# ----------------------------------------------------------------------
# playback_cartographer.sh — 离线回放同一 bag 给 Cartographer（阶段 13）
# ----------------------------------------------------------------------
# 前置：无仿真运行（回放前自动清理残留 SLAM 节点）。
# 用法：bash playback_cartographer.sh <bag目录>
# 输出：results/时间戳/cartographer/{cpu_memory.csv, map.pgm, map.yaml, summary.json}
# ----------------------------------------------------------------------
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
# 先 source 再开 set -u（ament 脚本在严格模式下报未绑定变量）
source /opt/ros/humble/setup.bash
source "$ROOT/install/setup.bash"
set -u

BAG="${1:?用法: playback_cartographer.sh <bag目录>}"
if [ ! -d "$BAG" ]; then
    echo "FAIL: bag 不存在: $BAG"
    exit 1
fi

EXPERIMENT_DIR="$ROOT/src/diy_nav_slam_compare/results/$(date +%Y%m%d_%H%M%S)"
ALGO_DIR="$EXPERIMENT_DIR/cartographer"
mkdir -p "$ALGO_DIR"
LOG="/tmp/playback_carto.log"

echo "== 清理残留 SLAM 节点 =="
ps aux | /usr/bin/grep -E "async_slam_toolbox|cartographer_node|occupancy_grid" | /usr/bin/grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
sleep 2

echo "== 启动 Cartographer（use_sim_time，离线回放） =="
ros2 launch diy_nav_slam_compare cartographer.launch.py rviz:=false \
    > "$LOG" 2>&1 &
CARTO_PID=$!
sleep 8

CARTO_NODE_PID=$(ps aux | /usr/bin/grep "[c]artographer_node" | awk '{print $2}' | head -1)
echo "cartographer pid=$CARTO_NODE_PID"

python3 "$ROOT/src/diy_nav_slam_compare/scripts/resource_monitor.py" \
    --pid "$CARTO_NODE_PID" --interval 2.0 --duration 1200 \
    --output "$ALGO_DIR/cpu_memory.csv" &
MON_PID=$!

echo "== 回放 bag（--clock 提供仿真时间） =="
ros2 bag play "$BAG" --clock --rate 1.0
echo "== 回放结束 =="
sleep 5

kill "$MON_PID" 2>/dev/null
python3 "$ROOT/src/diy_nav_navigation/scripts/save_map.py" \
    "$ALGO_DIR/map" 2>/dev/null || true
python3 "$ROOT/src/diy_nav_slam_compare/scripts/map_statistics.py" \
    --map "$ALGO_DIR/map.pgm" --output "$ALGO_DIR/summary.json" || true

kill -INT -- "-$CARTO_PID" 2>/dev/null
ps aux | /usr/bin/grep -E "[c]artographer_node|[o]ccupancy_grid" | awk '{print $2}' | xargs -r kill -9 2>/dev/null

echo "ALGO_DIR=$ALGO_DIR"
