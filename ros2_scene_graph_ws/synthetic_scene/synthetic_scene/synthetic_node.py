import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2, CameraInfo, PointField
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
from cv_bridge import CvBridge
import numpy as np
import os

# Custom messages
from scene_graph_msgs.msg import SceneGraph, SceneObject

# Utilities
from .scene_loader import load_scene
from .open3d_renderer import SceneRenderer
from .pointcloud_utils import depth_to_pointcloud

class SyntheticSceneNode(Node):
    def __init__(self):
        super().__init__('synthetic_scene_node')
        
        # Parameters
        self.declare_parameter('scene_config_path', 'config/scene_config.yaml')
        config_path = self.get_parameter('scene_config_path').get_parameter_value().string_value
        
        # Resolve path relative to workspace root if necessary
        # Assuming we run from ros2_scene_graph_ws
        if not os.path.isabs(config_path):
            config_path = os.path.abspath(config_path)

        self.get_logger().info(f"Loading scene from {config_path}")
        self.scene_data = load_scene(config_path)
        
        # Initialize Renderer
        cam_cfg = self.scene_data['camera']
        self.renderer = SceneRenderer(
            self.scene_data, 
            cam_cfg['image_width'], 
            cam_cfg['image_height'], 
            cam_cfg['fov_deg']
        )
        
        # Publishers
        self.pub_rgb = self.create_publisher(Image, '/rgb_image', 10)
        self.pub_depth = self.create_publisher(Image, '/depth', 10)
        self.pub_pc = self.create_publisher(PointCloud2, '/pointcloud', 10)
        self.pub_info = self.create_publisher(CameraInfo, '/camera_info', 10)
        self.pub_gt = self.create_publisher(SceneGraph, '/ground_truth/objects', 1)
        
        # TF Broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)
        
        self.bridge = CvBridge()
        
        # Timers
        self.timer_sensors = self.create_timer(0.1, self.timer_sensors_callback)  # 10 Hz
        self.timer_gt = self.create_timer(1.0, self.timer_gt_callback)           # 1 Hz

    def timer_sensors_callback(self):
        cam_cfg = self.scene_data['camera']
        cam_pos = cam_cfg['position']
        look_at = cam_cfg['look_at']
        
        # 1. Render
        rgb, depth = self.renderer.render(cam_pos, look_at)
        
        # 2. Publish RGB
        rgb_msg = self.bridge.cv2_to_imgmsg(rgb, encoding="rgb8")
        rgb_msg.header.stamp = self.get_clock().now().to_msg()
        rgb_msg.header.frame_id = "camera_link"
        self.pub_rgb.publish(rgb_msg)
        
        # 3. Publish Depth
        depth_msg = self.bridge.cv2_to_imgmsg(depth, encoding="32FC1")
        depth_msg.header.stamp = rgb_msg.header.stamp
        depth_msg.header.frame_id = "camera_link"
        self.pub_depth.publish(depth_msg)
        
        # 4. Publish PointCloud
        intrinsics = self.renderer.get_camera_intrinsics()
        pts = depth_to_pointcloud(depth, intrinsics)
        pc_msg = self.create_pc2_msg(pts, rgb_msg.header.stamp, "camera_link")
        self.pub_pc.publish(pc_msg)
        
        # 5. Publish CameraInfo
        info_msg = CameraInfo()
        info_msg.header = rgb_msg.header
        info_msg.width = intrinsics['width']
        info_msg.height = intrinsics['height']
        info_msg.k = [
            intrinsics['fx'], 0.0, intrinsics['cx'],
            0.0, intrinsics['fy'], intrinsics['cy'],
            0.0, 0.0, 1.0
        ]
        self.pub_info.publish(info_msg)
        
        # 6. Broadcast TF: world -> camera_link
        t = TransformStamped()
        t.header.stamp = rgb_msg.header.stamp
        t.header.frame_id = "world"
        t.child_frame_id = "camera_link"
        t.transform.translation.x = float(cam_pos[0])
        t.transform.translation.y = float(cam_pos[1])
        t.transform.translation.z = float(cam_pos[2])
        # For simplicity, identity rotation for now or compute from look_at
        # In a real system, you'd use a proper quaternion.
        t.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(t)

    def timer_gt_callback(self):
        msg = SceneGraph()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "world"
        
        all_objs = self.scene_data['objects'] + self.scene_data['near_miss_objects']
        for obj in all_objs:
            so = SceneObject()
            so.object_id = obj['id']
            so.semantic_label = obj['label']
            so.position_xyz = [float(x) for x in obj['position']]
            
            # Compute bbox min/max from position and size
            pos = np.array(obj['position'])
            size = np.array(obj['size'])
            so.bbox_min_xyz = (pos - size/2).tolist()
            so.bbox_max_xyz = (pos + size/2).tolist()
            
            so.is_dynamic = False  # Static ground truth
            so.ib_cluster_id = ""
            msg.objects.append(so)
        
        self.pub_gt.publish(msg)

    def create_pc2_msg(self, points, stamp, frame_id):
        """Helper to create sensor_msgs/PointCloud2 from Nx3 numpy array."""
        msg = PointCloud2()
        msg.header.stamp = stamp
        msg.header.frame_id = frame_id
        msg.height = 1
        msg.width = points.shape[0]
        msg.is_dense = True
        msg.is_bigendian = False
        msg.fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        msg.point_step = 12
        msg.row_step = msg.point_step * points.shape[0]
        msg.data = points.tobytes()
        return msg

def main(args=None):
    rclpy.init(args=args)
    node = SyntheticSceneNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
