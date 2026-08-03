# 系统架构（system_architecture.md）

## 1. 系统节点图

```mermaid
flowchart LR
    subgraph Gazebo["Gazebo Classic 11（仿真物理世界）"]
        GS[gzserver]
        GC[gzclient]
        subgraph Models["模型与插件"]
            ROBOT[机器人模型 diy_nav_bot]
            DIFF[libgazebo_ros_diff_drive]
            LASER[libgazebo_ros_ray_sensor]
            IMUP[libgazebo_ros_imu_sensor]
            JSP[libgazebo_ros_joint_state_publisher]
        end
    end

    RSP[robot_state_publisher]
    SF[scan_filter（自遮挡抑制 + QoS 双发布）]

    subgraph Mapping["SLAM 模式（二选一，互斥保护）"]
        ST[slam_toolbox]
        CA[cartographer_node]
    end

    subgraph Nav["导航模式"]
        MS[map_server]
        AMCL[amcl]
        CS[controller_server]
        PS[planner_server]
        BT[bt_navigator]
        BS[behavior_server]
        VS[velocity_smoother]
        WF[waypoint_follower]
    end

    RV[RViz2]

    GS --> DIFF & LASER & IMUP & JSP
    DIFF --> |/odom /tf| SF
    LASER --> |/scan_raw| SF
    SF --> |/scan_slam| ST & CA
    SF --> |/scan| AMCL & CS & PS
    RSP --> |/tf_static| ST & CA & AMCL
    ST --> |/map map→odom| RV
    CA --> |/map map→odom| RV
    MS --> |/map| AMCL & CS & PS
    AMCL --> |map→odom| CS & PS
    CS --> |/cmd_vel| VS
    VS --> |/cmd_vel| DIFF
```

## 2. Topic 数据流图

```mermaid
flowchart LR
    DIFF[差速驱动] -->|/odom nav_msgs/Odometry| AMCL
    DIFF -->|/tf odom→base_footprint| ALL
    LASER[激光] -->|/scan_raw| SF[scan_filter]
    SF -->|/scan 过滤后 10Hz| AMCL & CM[costmap]
    SF -->|/scan_slam RELIABLE| SLAM[SLAM Toolbox / Cartographer]
    SLAM -->|/map| MS[map_server → AMCL/静态层]
    SLAM -->|/map| RV[RViz]
    AMCL -->|/amcl_pose| RV
    PS[planner_server] -->|/plan| CS[controller_server]
    CS -->|/cmd_vel| VS[velocity_smoother] -->|/cmd_vel| DIFF
```

## 3. TF 树

```mermaid
graph TD
    MAP[map] -->|AMCL 或 SLAM 发布| ODOM[odom]
    ODOM -->|差速驱动发布| BF[base_footprint]
    BF -->|robot_state_publisher| BL[base_link]
    BL --> LW[left_wheel_link]
    BL --> RW[right_wheel_link]
    BL --> FC[front_caster_link]
    BL --> LZ[laser_link]
    BL --> IMU[imu_link]
```

TF 单一来源原则：`odom → base_footprint` 仅由差速驱动发布；`map → odom`
仅由 AMCL 或 SLAM（互斥运行）发布；其余由 robot_state_publisher 发布；
无任何静态 TF 伪造。

## 4. Nav2 工作流程

```mermaid
sequenceDiagram
    participant U as 用户/RViz
    participant BT as bt_navigator
    participant PS as planner_server
    participant CS as controller_server
    participant AM as AMCL
    participant R as 机器人

    U->>BT: NavigateToPose(目标)
    BT->>PS: ComputePathToPose
    PS->>PS: 全局代价地图 + NavFn 规划
    PS-->>BT: 全局路径
    BT->>CS: FollowPath
    CS->>CS: 局部代价地图 + DWB 采样
    CS->>R: /cmd_vel（经 velocity_smoother）
    R-->>AM: /odom /scan
    AM-->>CS: map→odom（定位反馈）
    CS-->>BT: 进度反馈
    BT->>BS: 卡死时触发恢复（spin/backup）
```

## 5. SLAM 工作流程（两种方案共用数据）

```mermaid
flowchart LR
    BAG[同一 rosbag：/scan_slam /odom /tf /clock] -->|离线回放 --clock| ST[SLAM Toolbox]
    BAG -->|离线回放 --clock| CA[Cartographer]
    ST -->|地图| M1[map.pgm/yaml]
    CA -->|地图| M2[map.pgm/yaml]
    M1 --> NAV[Nav2 5目标×3次]
    M2 --> NAV
    NAV --> R[导航成功率/耗时/恢复次数]
```
