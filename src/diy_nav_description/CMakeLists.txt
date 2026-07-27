# diy_nav_description
# 机器人 URDF/Xacro 描述、meshes、RViz 配置与 display launch。
# 该包不包含 C++/Python 源码，仅安装资源目录与验证脚本。
cmake_minimum_required(VERSION 3.8)
project(diy_nav_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 查找构建工具
find_package(ament_cmake REQUIRED)

# ------------------------------------------------------------
# 安装资源目录到 share/${PROJECT_NAME}/
# ------------------------------------------------------------
install(
  DIRECTORY
    launch
    urdf
    meshes
    rviz
  DESTINATION share/${PROJECT_NAME}/
)

# README 直接放到 share 顶层，便于用户从 install 路径查阅
install(
  FILES README.md
  DESTINATION share/${PROJECT_NAME}/
)

# ------------------------------------------------------------
# 安装可执行验证脚本到 lib/${PROJECT_NAME}
# ros2 run diy_nav_description validate_description.sh 可调用
# ------------------------------------------------------------
install(
  PROGRAMS scripts/validate_description.sh
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # 骨架阶段暂无版权声明，跳过 copyright 检查
  set(ament_cmake_copyright_FOUND TRUE)
  # 骨架阶段尚未初始化为 git 仓库时跳过 cpplint
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
