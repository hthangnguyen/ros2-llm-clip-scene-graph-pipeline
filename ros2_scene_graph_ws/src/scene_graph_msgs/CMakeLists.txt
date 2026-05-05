cmake_minimum_required(VERSION 3.8)
project(scene_graph_msgs)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/SceneObject.msg"
  "msg/SceneGraph.msg"
  "msg/TrajectoryHeatmap.msg"
  "msg/ObjectEmbeddings.msg"
  "msg/DynamicFlags.msg"
  DEPENDENCIES std_msgs builtin_interfaces
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
