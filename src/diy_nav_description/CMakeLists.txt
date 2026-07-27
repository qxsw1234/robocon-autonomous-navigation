# diy_nav_description
# 机器人 URDF/Xacro 描述、meshes 与 RViz 配置包。
# 该包不包含 C++/Python 源码，仅安装资源目录。
cmake_minimum_required(VERSION 3.8)
project(diy_nav_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 查找构建工具
find_package(ament_cmake REQUIRED)

# 安装资源目录到 share/${PROJECT_NAME}/
# 使用 DIRECTORY 形式；缺失目录不会导致失败（CMake 会跳过空目录）
install(
  DIRECTORY
    launch
    urdf
    meshes
    rviz
  DESTINATION share/${PROJECT_NAME}/
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
