# diy_nav_navigation
# Navigation2 启动文件、参数 YAML、静态地图与行为树 XML。
# 该包不包含 C++/Python 源码，仅安装资源目录。
cmake_minimum_required(VERSION 3.8)
project(diy_nav_navigation)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

# 安装资源目录
install(
  DIRECTORY
    launch
    config
    maps
    rviz
    behavior_trees
  DESTINATION share/${PROJECT_NAME}/
)

# 安装脚本目录（可执行辅助脚本），使用 PROGRAMS 保留可执行位
install(
  DIRECTORY scripts/
  DESTINATION lib/${PROJECT_NAME}
  USE_SOURCE_PERMISSIONS
  FILES_MATCHING
    PATTERN "*"
    PATTERN "*.md" EXCLUDE
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
