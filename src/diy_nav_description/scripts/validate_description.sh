#!/usr/bin/env bash
# ----------------------------------------------------------------------
# validate_description.sh
# ----------------------------------------------------------------------
# Static validation of the diy_nav_bot URDF/Xacro model.
#
# Checks:
#   1. ROS 2 environment sourced (ROS_DISTRO=humble)
#   2. diy_nav_description package discoverable
#   3. Main Xacro file exists
#   4. Xacro expansion succeeds
#   5. check_urdf passes on expanded URDF
#   6. Required links / joints present
#   7. No leftover xacro: tags
#   8. No forbidden gazebo/nav/slam content (frame-precise)
#   9. Structural XML checks via Python (uniqueness, parents, single-parent)
#  10. TF root == base_footprint
#
# Stage awareness:  --stage N  (default 4)
#   N < 5 : Gazebo plugin tokens are forbidden (pure URDF stages)
#   N >= 5: Gazebo plugin tokens allowed (urdf/gazebo_plugins.xacro implements
#           the Gazebo plugins from stage 5 on)
#   slam_toolbox / cartographer tokens are forbidden in every stage.
#
# Uses only bash + coreutils + a small Python XML pass. Does NOT rely on
# `set -e`, so partial failures still print later results. Final exit code
# is nonzero if any FAIL is recorded.
# ----------------------------------------------------------------------
set -uo pipefail

PACKAGE_NAME="diy_nav_description"
MAIN_XACRO_RELPATH="urdf/diy_nav_bot.urdf.xacro"

# Use full paths for tools that may be shadowed by ZCode wrappers.
GREP=/usr/bin/grep

# ---------- 阶段参数 ----------
# --stage N（默认 4）：N>=5 时解锁 Gazebo 插件 token 检查。
STAGE=4
if [ "${1:-}" = "--stage" ]; then
  STAGE="${2:-4}"
fi
case "${STAGE}" in
  ''|*[!0-9]*) echo "[ERROR] --stage 需要非负整数参数（当前: '${STAGE}'）"; exit 2 ;;
esac
info()  { printf '[INFO] %s\n'  "$*"; }
info "Validation stage: ${STAGE}"

REQUIRED_LINKS=(
  base_footprint
  base_link
  chassis_link
  upper_body_link
  left_wheel_link
  right_wheel_link
  front_caster_link
  laser_mount_link
  laser_link
  imu_link
)

REQUIRED_JOINTS=(
  base_footprint_to_base_link
  base_link_to_chassis
  chassis_to_upper_body
  left_wheel_joint
  right_wheel_joint
  front_caster_joint
  laser_mount_joint
  laser_joint
  imu_joint
)

# 阶段 5 起解锁的 Gazebo 插件 token（随 gazebo_plugins.xacro 填充实现出现）
GAZEBO_PLUGIN_TOKENS=(
  # Gazebo plugin filenames
  libgazebo_ros_diff_drive.so
  libgazebo_ros_ray_sensor.so
  libgazebo_ros_imu_sensor.so
  libgazebo_ros_laser.so
  gazebo_ros_diff_drive
)

# 任何阶段都禁止出现在 description 包中的内容
ALWAYS_FORBIDDEN_TOKENS=(
  # SLAM / Nav
  slam_toolbox
  cartographer
)

FORBIDDEN_TOKENS=("${ALWAYS_FORBIDDEN_TOKENS[@]}")
if [ "${STAGE}" -lt 5 ]; then
  FORBIDDEN_TOKENS+=("${GAZEBO_PLUGIN_TOKENS[@]}")
  GAZEBO_NOTE="stage ${STAGE} < 5: gazebo plugin tokens still forbidden"
else
  GAZEBO_NOTE="stage ${STAGE} >= 5: gazebo plugin tokens unlocked"
fi

FAILS=0
WARNS=0

pass()  { printf '[PASS] %s\n'  "$*"; }
warn()  { printf '[WARN] %s\n'  "$*"; WARNS=$((WARNS+1)); }
fail()  { printf '[FAIL] %s\n'  "$*"; FAILS=$((FAILS+1)); }
info()  { printf '[INFO] %s\n'  "$*"; }

# ---------- 1. ROS environment ----------
if [ "${ROS_DISTRO:-}" = "humble" ]; then
  pass "ROS_DISTRO=humble"
else
  fail "ROS_DISTRO=${ROS_DISTRO:-NOT_SET} (expected humble)"
fi

# ---------- 2. Package discovery ----------
PKG_PREFIX=""
if command -v ros2 >/dev/null 2>&1; then
  PKG_PREFIX="$(ros2 pkg prefix "${PACKAGE_NAME}" 2>/dev/null || true)"
fi
if [ -n "${PKG_PREFIX}" ] && [ -d "${PKG_PREFIX}" ]; then
  pass "ros2 pkg prefix ${PACKAGE_NAME} = ${PKG_PREFIX}"
else
  fail "Cannot locate installed ${PACKAGE_NAME}; run colcon build first"
fi

# ---------- 3. Main Xacro path ----------
MAIN_XACRO=""
if [ -n "${PKG_PREFIX}" ] && [ -f "${PKG_PREFIX}/share/${PACKAGE_NAME}/${MAIN_XACRO_RELPATH}" ]; then
  MAIN_XACRO="${PKG_PREFIX}/share/${PACKAGE_NAME}/${MAIN_XACRO_RELPATH}"
  pass "Main Xacro (install space): ${MAIN_XACRO}"
elif [ -f "${HOME}/ros2_ws/src/${PACKAGE_NAME}/${MAIN_XACRO_RELPATH}" ]; then
  MAIN_XACRO="${HOME}/ros2_ws/src/${PACKAGE_NAME}/${MAIN_XACRO_RELPATH}"
  warn "Falling back to source-tree Xacro: ${MAIN_XACRO}"
else
  fail "Cannot find ${MAIN_XACRO_RELPATH}"
fi

# ---------- 4. Xacro expansion ----------
URDF_TMP="$(mktemp -t diy_nav_bot_XXXXXX.urdf)"
if [ -n "${MAIN_XACRO}" ] && xacro "${MAIN_XACRO}" > "${URDF_TMP}" 2>/tmp/validate_xacro_err.txt; then
  pass "Xacro expansion succeeded ($(wc -l < "${URDF_TMP}") lines)"
else
  fail "Xacro expansion failed. stderr:"
  sed 's/^/       /' /tmp/validate_xacro_err.txt
fi

# ---------- 5. check_urdf ----------
if [ -s "${URDF_TMP}" ]; then
  if check_urdf "${URDF_TMP}" > /tmp/validate_check_urdf.txt 2>&1; then
    pass "check_urdf succeeded"
  else
    fail "check_urdf failed:"
    sed 's/^/       /' /tmp/validate_check_urdf.txt
  fi
fi

# ---------- 6. Required links ----------
if [ -s "${URDF_TMP}" ]; then
  MISSING_LINKS=()
  for lk in "${REQUIRED_LINKS[@]}"; do
    if ! "${GREP}" -qE "<link[[:space:]]+name=\"${lk}\"" "${URDF_TMP}"; then
      MISSING_LINKS+=("${lk}")
    fi
  done
  if [ "${#MISSING_LINKS[@]}" -eq 0 ]; then
    pass "All ${#REQUIRED_LINKS[@]} required links present"
  else
    fail "Missing link(s): ${MISSING_LINKS[*]}"
  fi

  # ---------- 7. Required joints ----------
  MISSING_JOINTS=()
  for jt in "${REQUIRED_JOINTS[@]}"; do
    if ! "${GREP}" -qE "<joint[[:space:]]+name=\"${jt}\"" "${URDF_TMP}"; then
      MISSING_JOINTS+=("${jt}")
    fi
  done
  if [ "${#MISSING_JOINTS[@]}" -eq 0 ]; then
    pass "All ${#REQUIRED_JOINTS[@]} required joints present"
  else
    fail "Missing joint(s): ${MISSING_JOINTS[*]}"
  fi
fi

# ---------- 8. Leftover xacro tags ----------
if [ -s "${URDF_TMP}" ]; then
  UNRESOLVED="$( "${GREP}" -c 'xacro:' "${URDF_TMP}" || true )"
  if [ "${UNRESOLVED:-0}" -eq 0 ]; then
    pass "No unresolved xacro: tags in expanded URDF"
  else
    fail "Found ${UNRESOLVED} unresolved xacro: token(s)"
  fi
fi

# ---------- 9. Forbidden tokens ----------
if [ -s "${URDF_TMP}" ]; then
  BAD_HITS=()
  for tok in "${FORBIDDEN_TOKENS[@]}"; do
    if "${GREP}" -q "${tok}" "${URDF_TMP}"; then
      BAD_HITS+=("${tok}")
    fi
  done
  if [ "${#BAD_HITS[@]}" -eq 0 ]; then
    pass "No forbidden gazebo/nav/slam tokens present (${GAZEBO_NOTE})"
  else
    fail "Forbidden token(s) found: ${BAD_HITS[*]} (${GAZEBO_NOTE})"
  fi

  # Precise check: no <link name="map"|"odom"> and no <joint name="map"|"odom">
  if "${GREP}" -qE '<link[[:space:]]+name="(map|odom)"' "${URDF_TMP}" || \
     "${GREP}" -qE '<joint[[:space:]]+name="(map|odom)"' "${URDF_TMP}"; then
    fail 'Forbidden frame name "map" or "odom" appears in URDF (link or joint)'
  else
    pass 'No <link|joint name="map"|"odom"> in URDF'
  fi
fi

# ---------- 10. Python XML structural pass ----------
if [ -s "${URDF_TMP}" ]; then
  python3 - "${URDF_TMP}" <<'PY' >/tmp/validate_py.txt 2>&1
import sys
import xml.etree.ElementTree as ET

path = sys.argv[1]
tree = ET.parse(path)
root = tree.getroot()

links = [e.get('name') for e in root.iter('link')]
joints = [e.get('name') for e in root.iter('joint')]

problems = []

# unique names
def dupes(seq):
    seen = set()
    dup = []
    for s in seq:
        if s in seen:
            dup.append(s)
        seen.add(s)
    return dup

dup_l = dupes(links)
dup_j = dupes(joints)
if dup_l:
    problems.append(f'Duplicate link name(s): {dup_l}')
if dup_j:
    problems.append(f'Duplicate joint name(s): {dup_j}')

# parents/children valid
link_set = set(links)
parents_of = {}  # child -> [joint names]
for j in root.iter('joint'):
    jname = j.get('name')
    p = j.find('parent')
    c = j.find('child')
    if p is None or c is None:
        problems.append(f'Joint {jname} missing parent/child')
        continue
    parent = p.get('link')
    child = c.get('link')
    if parent not in link_set:
        problems.append(f'Joint {jname} parent "{parent}" not a defined link')
    if child not in link_set:
        problems.append(f'Joint {jname} child "{child}" not a defined link')
    parents_of.setdefault(child, []).append(jname)

# each non-root link has exactly one parent joint
multi_parent = {c: js for c, js in parents_of.items() if len(js) > 1}
if multi_parent:
    problems.append(f'Link(s) with multiple parent joints: {multi_parent}')

# root of TF tree: link that never appears as a child
roots = [lk for lk in link_set if lk not in parents_of]
if len(roots) != 1:
    problems.append(f'Expected exactly one TF root, got: {roots}')
else:
    if roots[0] != 'base_footprint':
        problems.append(f'TF root is "{roots[0]}", expected "base_footprint"')

# All inertials positive-definite (diagonal > 0), non-NaN
import math
for lk in root.iter('link'):
    inertial = lk.find('inertial')
    if inertial is None:
        continue
    m = inertial.find('mass')
    if m is None or float(m.get('value', '0')) <= 0:
        problems.append(f'Link {lk.get("name")}: mass <= 0 or missing')
    it = inertial.find('inertia')
    if it is None:
        problems.append(f'Link {lk.get("name")}: <inertia> missing')
        continue
    for k in ('ixx', 'iyy', 'izz'):
        v = float(it.get(k, '0'))
        if math.isnan(v) or math.isinf(v) or v <= 0:
            problems.append(f'Link {lk.get("name")}: {k}={v}')

if problems:
    print('STRUCTURAL_FAIL')
    for p in problems:
        print(f'  - {p}')
else:
    print(f'STRUCTURAL_OK links={len(links)} joints={len(joints)} root=base_footprint')
PY
  py_rc=$?
  py_out="$(cat /tmp/validate_py.txt)"
  if [ ${py_rc} -eq 0 ] && [[ "${py_out}" == STRUCTURAL_OK* ]]; then
    pass "Structural XML checks: ${py_out#STRUCTURAL_OK }"
  else
    fail "Structural XML checks:"
    echo "${py_out}" | sed 's/^/       /'
  fi
fi

# ---------- 11. Optional mesh dir check ----------
if [ -n "${PKG_PREFIX}" ]; then
  MESH_DIR="${PKG_PREFIX}/share/${PACKAGE_NAME}/meshes"
  if [ -d "${MESH_DIR}" ]; then
    if [ -z "$(ls -1 "${MESH_DIR}" 2>/dev/null | "${GREP}" -v '^\.gitkeep$' | head -n1)" ]; then
      warn "Mesh directory is currently empty (${MESH_DIR})"
    else
      pass "Mesh directory contains files"
    fi
  fi
fi

# ---------- Summary ----------
echo ""
echo "===================================================="
if [ "${FAILS}" -eq 0 ]; then
  echo "VALIDATION SUMMARY: ${FAILS} FAIL, ${WARNS} WARN  -> OK"
  exit 0
else
  echo "VALIDATION SUMMARY: ${FAILS} FAIL, ${WARNS} WARN  -> FAILED"
  exit 1
fi
