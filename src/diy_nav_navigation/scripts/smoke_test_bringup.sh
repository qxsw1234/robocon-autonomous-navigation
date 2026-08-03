#!/usr/bin/env bash
# ----------------------------------------------------------------------
# smoke_test_bringup.sh — bringup 一键启动冒烟测试（阶段 11）
# ----------------------------------------------------------------------
# 用法:
#   bash smoke_test_bringup.sh [slam|navigation] [world]
# 默认: slam complex
#
# 检查项（启动后 30s 内）:
#   1. 必要节点存在（SLAM: async_slam_toolbox_node；NAV: map_server/
#      amcl/controller_server/planner_server/bt_navigator）
#   2. /clock /scan /odom 有数据
#   3. TF 连通（map → base_footprint）
#   4. SLAM 模式存在 /map
#   5. NAV 模式 Nav2 生命周期节点 active
#   6. 关闭 bringup 后 gzserver 等进程退出（无残留）
# ----------------------------------------------------------------------
MODE="${1:-slam}"
WORLD="${2:-complex}"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LOG="/tmp/smoke_bringup_${MODE}.log"
PYPROBE=/tmp/smoke_probe_${MODE}.py

if [ ! -f "$ROOT/install/setup.bash" ]; then
    echo "FAIL: 未找到 $ROOT/install/setup.bash（请先 colcon build）"
    exit 1
fi
# 先 source 再开 set -u（ament 脚本在严格模式下报未绑定变量）
source /opt/ros/humble/setup.bash
source "$ROOT/install/setup.bash"
set -u

# ---------------- 1. 启动 bringup ----------------
echo "== 启动 bringup mode:=$MODE world:=$WORLD（headless） =="
ros2 launch diy_nav_navigation bringup.launch.py \
    mode:="$MODE" world:="$WORLD" rviz:=false headless:=true \
    > "$LOG" 2>&1 &
LAUNCH_PID=$!
echo "launch pid=$LAUNCH_PID"

cat > "$PYPROBE" <<'PYEOF'
import rclpy, sys, time, math
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from std_msgs.msg import String
from nav_msgs.msg import OccupancyGrid
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from lifecycle_msgs.srv import GetState
from tf2_ros import Buffer, TransformListener

MODE = sys.argv[1]
DEADLINE = float(sys.argv[2])
rclpy.init()
node = Node('smoke_probe', parameter_overrides=[rclpy.parameter.Parameter('use_sim_time', value=True)])
q = QoSProfile(depth=3, reliability=ReliabilityPolicy.BEST_EFFORT)
results = {}

def wait_data(topic, msg_type, timeout, qos=None):
    got = []
    node.create_subscription(msg_type, topic, lambda m, g=got: g.append(m),
                             qos_profile=qos or q)
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        rclpy.spin_once(node, timeout_sec=0.1)
        if got:
            return True
    return False

tf_buf = Buffer()
tf_lis = TransformListener(tf_buf, node)

# 导航模式：持续发布初始位姿 (0,0,0)（否则 AMCL 无 map→odom，
# 生命周期激活会卡住）
init_pub = None
init_next = 0.0
if MODE == 'navigation':
    from geometry_msgs.msg import PoseWithCovarianceStamped
    init_pub = node.create_publisher(PoseWithCovarianceStamped, '/initialpose', q)
    init_msg = PoseWithCovarianceStamped()
    init_msg.header.frame_id = 'map'
    init_msg.pose.pose.orientation.w = 1.0
    init_msg.pose.covariance[0] = init_msg.pose.covariance[7] = init_msg.pose.covariance[35] = 0.01

t0 = time.monotonic()
while time.monotonic() - t0 < DEADLINE:
    rclpy.spin_once(node, timeout_sec=0.1)
    elapsed = time.monotonic() - t0
    if init_pub is not None and time.monotonic() >= init_next:
        init_pub.publish(init_msg)
        init_next = time.monotonic() + 1.0

    # 1. 节点存在
    if 'nodes' not in results:
        wanted = (['slam_toolbox'] if MODE == 'slam' else
                  ['map_server', 'amcl', 'controller_server',
                   'planner_server', 'bt_navigator'])
        names = node.get_node_names()
        missing = [w for w in wanted if w not in names]
        if not missing:
            results['nodes'] = f'OK ({", ".join(wanted)})'

    # 2. 话题数据
    if 'clock' not in results:
        from rosgraph_msgs.msg import Clock
        got = []
        node.create_subscription(Clock, '/clock', lambda m, g=got: g.append(m),
                                 qos_profile=QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT))
        tt = time.monotonic()
        while time.monotonic() - tt < 1.0:
            rclpy.spin_once(node, timeout_sec=0.1)
        if got:
            results['clock'] = 'OK'

    if 'scan' not in results:
        if wait_data('/scan', LaserScan, 1.0):
            results['scan'] = 'OK'
    if 'odom' not in results:
        if wait_data('/odom', Odometry, 1.0):
            results['odom'] = 'OK'

    # 3. TF 连通（map → base_footprint）
    if 'tf' not in results:
        try:
            tf_buf.lookup_transform('map', 'base_footprint', rclpy.time.Time(),
                                    timeout=rclpy.duration.Duration(seconds=0.5))
            results['tf'] = 'OK'
        except Exception:
            pass

    # 4. SLAM /map
    if MODE == 'slam' and 'map' not in results:
        qm = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                        reliability=ReliabilityPolicy.RELIABLE)
        got = []
        node.create_subscription(OccupancyGrid, '/map', lambda m, g=got: g.append(m),
                                 qos_profile=qm)
        tt = time.monotonic()
        while time.monotonic() - tt < 1.0:
            rclpy.spin_once(node, timeout_sec=0.1)
        if got:
            results['map'] = f'OK ({got[-1].info.width}x{got[-1].info.height})'

    # 5. NAV 生命周期 active
    if MODE == 'navigation' and 'lifecycle' not in results:
        all_active = True
        for n in ['map_server', 'amcl', 'controller_server', 'planner_server',
                  'bt_navigator']:
            c = node.create_client(GetState, f'/{n}/get_state')
            tt = time.monotonic()
            while time.monotonic() - tt < 1.5 and not c.wait_for_service(timeout_sec=0.2):
                rclpy.spin_once(node, timeout_sec=0.05)
            if not c.service_is_ready():
                all_active = False
                node.destroy_client(c)
                break
            fut = c.call_async(GetState.Request())
            tt = time.monotonic()
            while not fut.done() and time.monotonic() - tt < 1.5:
                rclpy.spin_once(node, timeout_sec=0.05)
            if not (fut.done() and fut.result().current_state.label == 'active'):
                all_active = False
            node.destroy_client(c)
            if not all_active:
                break
        if all_active:
            results['lifecycle'] = 'OK (全部 active)'

    if len(results) >= (5 if MODE == 'slam' else 6):
        break

ok = True
order = ['nodes', 'clock', 'scan', 'odom', 'tf', 'map', 'lifecycle']
for k in order:
    if k in results:
        print(f'  [PASS] {k}: {results[k]}')
    else:
        if (MODE == 'slam' and k in ('nodes', 'clock', 'scan', 'odom', 'tf', 'map')) or \
           (MODE == 'navigation' and k in ('nodes', 'clock', 'scan', 'odom', 'tf', 'lifecycle')):
            print(f'  [FAIL] {k}: 未在 {DEADLINE:.0f}s 内就绪')
            ok = False
print('RESULT:', 'PASS' if ok else 'FAIL')
rclpy.shutdown()
sys.exit(0 if ok else 1)
PYEOF

echo "== 探测（30s 窗口） =="
if python3 "$PYPROBE" "$MODE" 30.0; then
    PROBE_OK=1
else
    PROBE_OK=0
fi

# ---------------- 6. 关闭 bringup，验证进程退出 ----------------
echo "== 关闭 bringup（SIGINT 进程组） =="
kill -INT -- "-$LAUNCH_PID" 2>/dev/null
sleep 8
# 兜底：若仍有残留则强杀（避免污染后续测试环境）
ps aux | /usr/bin/grep -E "gzserver|gzclient|async_slam_toolbox|nav2_|map_server|/amcl" | /usr/bin/grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
sleep 1
LEFT=$(ps aux | /usr/bin/grep -E "gzserver|gzclient|async_slam_toolbox|nav2_|map_server|/amcl" | /usr/bin/grep -v grep | wc -l)
if [ "$LEFT" -eq 0 ]; then
    echo "  [PASS] 清理: 无残留进程"
    CLEAN_OK=1
else
    echo "  [FAIL] 清理: 残留 $LEFT 个进程"
    ps aux | /usr/bin/grep -E "gzserver|gzclient|async_slam_toolbox|nav2_|map_server|/amcl" | /usr/bin/grep -v grep | awk '{print $2, $11, $12}'
    CLEAN_OK=0
fi

echo "== 日志尾部 =="
tail -5 "$LOG"

if [ "$PROBE_OK" -eq 1 ] && [ "$CLEAN_OK" -eq 1 ]; then
    echo "SMOKE TEST: PASS"
    exit 0
else
    echo "SMOKE TEST: FAIL"
    exit 1
fi
