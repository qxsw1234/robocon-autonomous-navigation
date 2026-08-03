#!/usr/bin/env bash
# ----------------------------------------------------------------------
# record_mapping_bag.sh — 录制建图数据 bag（阶段 13 公平对比）
# ----------------------------------------------------------------------
# 录制 /scan /odom /tf /tf_static /joint_states /imu /clock /cmd_vel，
# 同时运行 mapping_tour.py（固定 50 航点路线，两算法共用同一份数据）。
#
# 前置：simulation.launch.py 已启动（world:=complex，机器人已在 (0,0)）。
# 用法：bash record_mapping_bag.sh
# 输出：diy_nav_slam_compare/results/bags/mapping_YYYYMMDD_HHMMSS/
# ----------------------------------------------------------------------
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
# 先 source 再开 set -u（ament 脚本在严格模式下报未绑定变量）
source /opt/ros/humble/setup.bash
source "$ROOT/install/setup.bash"
set -u

BAG_DIR="$ROOT/src/diy_nav_slam_compare/results/bags"
mkdir -p "$BAG_DIR"
STAMP=$(date +%Y%m%d_%H%M%S)
BAG="$BAG_DIR/mapping_$STAMP"
LOG="/tmp/record_bag_$STAMP.log"

echo "== 开始录制 bag → $BAG =="
# /scan_slam 为算法实际订阅的 topic（RELIABLE 双发布），离线回放必需；
# /scan 一并录制（BE 版，供其他用途）
ros2 bag record /scan /scan_slam /odom /tf /tf_static /joint_states /imu /clock /cmd_vel \
    -o "$BAG" > "$LOG" 2>&1 &
REC_PID=$!

# 等 bag 节点就绪
sleep 5

echo "== 运行建图路线（50 航点） =="
python3 "$ROOT/src/diy_nav_navigation/scripts/mapping_tour.py" --no-map-check
TOUR_RC=$?

echo "== 建图路线结束（rc=$TOUR_RC），停止录制 =="
kill -INT "$REC_PID" 2>/dev/null
sleep 5
# 兜底
ps aux | /usr/bin/grep "[r]os2 bag record" | awk '{print $2}' | xargs -r kill 2>/dev/null

echo "== bag 信息 =="
ros2 bag info "$BAG" 2>/dev/null | head -15
echo "BAG_PATH=$BAG"
