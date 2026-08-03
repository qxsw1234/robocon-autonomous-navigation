-- ============================================================================
-- diy_nav_2d.lua — Cartographer 2D SLAM 配置（阶段 12）
-- 基线：官方 backpack_2d.lua（cartographer_ros 2.0.9），按项目约定修改：
--   * tracking_frame = "base_footprint"（REP-103 惯例，与 SLAM Toolbox 一致）
--   * published_frame = "odom"（把轨迹发布到 odom 系）
--   * provide_odom_frame = false（外部 /odom 由差速驱动提供，不重复发布）
--   * use_odometry = true（使用外部 /odom 里程计）
--   * use_imu_data = false（关闭 IMU——与只使用激光+里程计的 SLAM Toolbox
--     公平比较；后续可加一组启用 IMU 的附加实验）
--   * min_range/max_range 对齐激光与 scan_filter（0.30 ~ 8.0 m）
-- ============================================================================

include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "base_footprint",
  published_frame = "odom",
  odom_frame = "odom",
  provide_odom_frame = false,          -- 外部 /odom（差速驱动）已提供
  publish_frame_projected_to_2d = true,
  use_pose_extrapolator = true,
  use_odometry = true,                 -- 订阅 /odom 里程计
  use_nav_sat = false,
  use_landmarks = false,
  num_laser_scans = 1,                 -- 单线激光（/scan_slam）
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,
  lookup_transform_timeout_sec = 0.2,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,
  rangefinder_sampling_ratio = 1.,
  odometry_sampling_ratio = 1.,
  fixed_frame_pose_sampling_ratio = 1.,
  imu_sampling_ratio = 1.,
  landmarks_sampling_ratio = 1.,
}

MAP_BUILDER.use_trajectory_builder_2d = true

-- 公平比较：与 scan_filter 阈值 / 激光量程对齐
TRAJECTORY_BUILDER_2D.min_range = 0.30
TRAJECTORY_BUILDER_2D.max_range = 8.0
TRAJECTORY_BUILDER_2D.num_accumulated_range_data = 10

-- 与 SLAM Toolbox 对齐的关键开关：关闭 IMU（公平比较）
TRAJECTORY_BUILDER_2D.use_imu_data = false

return options
