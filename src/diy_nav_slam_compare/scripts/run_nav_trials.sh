#!/usr/bin/env bash
# ----------------------------------------------------------------------
# run_nav_trials.sh — 单地图导航试验（阶段 13：每图 5 目标 × 3 轮）
# ----------------------------------------------------------------------
# 用法：bash run_nav_trials.sh <algo: slam_toolbox|cartographer>
# 前置：无仿真运行。
# 流程：起仿真 → 定位(该算法地图) → 导航 → 初始位姿 → runner × 3 →
#       结果存 results/<实验目录>/navigation_trials_<algo>.csv
# ----------------------------------------------------------------------
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
# 先 source 再开 set -u
source /opt/ros/humble/setup.bash
source "$ROOT/install/setup.bash"
set -u

ALGO="${1:?用法: run_nav_trials.sh <slam_toolbox|cartographer>}"
EXP_DIR="$ROOT/src/diy_nav_slam_compare/results/20260803_174802"
MAP="$EXP_DIR/$ALGO/map.yaml"
RUNNER="$ROOT/src/diy_nav_navigation/scripts/nav_goal_runner.py"
INIT_SCRIPT=/tmp/init_and_activate_$$.py

echo "== 清理 =="
ps aux | /usr/bin/grep -E "gzserver|gzclient|nav2_|/amcl|/map_server|lifecycle|scan_filter|rviz2" | /usr/bin/grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
sleep 3

echo "== 启动仿真 =="
nohup ros2 launch diy_nav_gazebo simulation.launch.py world:=complex rviz:=false headless:=true > /tmp/trial_sim.log 2>&1 &
sleep 25

echo "== 启动定位（$ALGO 地图）+ 导航 =="
nohup ros2 launch diy_nav_navigation localization.launch.py rviz:=false map:="$MAP" > /tmp/trial_loc.log 2>&1 &
sleep 12
nohup ros2 launch diy_nav_navigation navigation.launch.py rviz:=false > /tmp/trial_nav.log 2>&1 &
sleep 22

cat > "$INIT_SCRIPT" <<'PYEOF'
import rclpy, time
from rclpy.qos import QoSProfile
from rclpy.parameter import Parameter
from geometry_msgs.msg import PoseWithCovarianceStamped
from lifecycle_msgs.srv import GetState, ChangeState
from lifecycle_msgs.msg import Transition
rclpy.init()
node = rclpy.create_node('trial_init', parameter_overrides=[Parameter('use_sim_time', value=True)])
q = QoSProfile(depth=5)
msg = PoseWithCovarianceStamped()
msg.header.frame_id = 'map'
msg.pose.pose.orientation.w = 1.0
msg.pose.covariance[0] = msg.pose.covariance[7] = msg.pose.covariance[35] = 0.01
pub = node.create_publisher(PoseWithCovarianceStamped, '/initialpose', q)
t_end = time.monotonic() + 25.0
while time.monotonic() < t_end:
    pub.publish(msg)
    rclpy.spin_once(node, timeout_sec=0.1)
    time.sleep(0.4)

def get_state(n):
    c = node.create_client(GetState, f'/{n}/get_state')
    t0 = time.monotonic()
    while time.monotonic() - t0 < 4.0 and not c.wait_for_service(timeout_sec=0.3):
        rclpy.spin_once(node, timeout_sec=0.1)
    if not c.service_is_ready():
        node.destroy_client(c); return None
    fut = c.call_async(GetState.Request())
    t0 = time.monotonic()
    while not fut.done() and time.monotonic() - t0 < 3.0:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_client(c)
    return fut.result().current_state.label if fut.done() else None

def set_state(n, tid):
    c = node.create_client(ChangeState, f'/{n}/change_state')
    t0 = time.monotonic()
    while time.monotonic() - t0 < 4.0 and not c.wait_for_service(timeout_sec=0.3):
        rclpy.spin_once(node, timeout_sec=0.1)
    if not c.service_is_ready():
        node.destroy_client(c); return False
    req = ChangeState.Request(); req.transition.id = tid
    fut = c.call_async(req)
    t0 = time.monotonic()
    while not fut.done() and time.monotonic() - t0 < 5.0:
        rclpy.spin_once(node, timeout_sec=0.1)
    ok = fut.done() and fut.result().success
    node.destroy_client(c)
    return ok

for n in ['map_server','amcl','controller_server','planner_server','behavior_server','bt_navigator','waypoint_follower','velocity_smoother']:
    st = get_state(n)
    if st in ('inactive', 'unconfigured'):
        if st == 'unconfigured':
            set_state(n, Transition.TRANSITION_CONFIGURE)
        set_state(n, Transition.TRANSITION_ACTIVATE)
print('初始位姿已发布，节点已激活')
rclpy.shutdown()
PYEOF
python3 "$INIT_SCRIPT"

echo "== 运行 runner × 3（$ALGO） =="
for i in 1 2 3; do
    echo "--- 第 $i 轮 ---"
    python3 "$RUNNER" \
        --output "$EXP_DIR/nav_goals_${ALGO}_run${i}.csv" \
        --initial-x 0 --initial-y 0 --initial-yaw 0
    sleep 5
done

echo "== 汇总 =="
python3 "$ROOT/src/diy_nav_slam_compare/scripts/navigation_result_logger.py" \
    --slam-csv $(ls "$EXP_DIR"/nav_goals_slam_toolbox_run*.csv 2>/dev/null) \
    --carto-csv $(ls "$EXP_DIR"/nav_goals_cartographer_run*.csv 2>/dev/null) \
    --output "$EXP_DIR/navigation_trials.csv" || true

echo "== 清理 =="
ps aux | /usr/bin/grep -E "gzserver|gzclient|nav2_|/amcl|/map_server|lifecycle|scan_filter|rviz2" | /usr/bin/grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
echo "DONE: $ALGO 导航试验完成"
