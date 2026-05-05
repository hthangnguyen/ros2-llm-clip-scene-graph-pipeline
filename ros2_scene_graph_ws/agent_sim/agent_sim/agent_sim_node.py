import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
from std_srvs.srv import Trigger
import os
import yaml
import signal

# Utilities
from .agent_path import AgentPath

class AgentSimNode(Node):
    def __init__(self):
        super().__init__('agent_sim_node')
        
        # Parameters
        self.declare_parameter('scene_config_path', 'config/scene_config.yaml')
        self.declare_parameter('primary_seed', 42)
        self.declare_parameter('sim_duration_sec', 120.0)
        
        config_path = self.get_parameter('scene_config_path').get_parameter_value().string_value
        primary_seed = self.get_parameter('primary_seed').get_parameter_value().integer_value
        self.duration = self.get_parameter('sim_duration_sec').get_parameter_value().double_value
        
        # Resolve config path
        if not os.path.isabs(config_path):
            config_path = os.path.abspath(config_path)
            
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        all_objs = config['scene']['objects'] + config['scene']['near_miss_objects']
        
        # Initialize paths for both agents
        self.agent_primary = AgentPath(config['agents'][0], all_objs, primary_seed)
        self.agent_secondary = AgentPath(config['agents'][1], all_objs, 0) # Deterministic secondary
        
        # Publishers
        self.pub_primary_pose = self.create_publisher(PoseStamped, '/agent_primary/pose', 10)
        self.pub_secondary_pose = self.create_publisher(PoseStamped, '/agent_secondary/pose', 10)
        self.pub_current_obj = self.create_publisher(String, '/agent_primary/current_object', 10)
        
        # Service
        self.srv_export = self.create_service(Trigger, '/agent_sim/export_trajectory', self.export_callback)
        
        # Simulation state
        self.sim_time = 0.0
        self.last_obj_id = None
        
        # Timer (10 Hz)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info(f"Agent simulation started with seed {primary_seed}")

    def timer_callback(self):
        if self.sim_time > self.duration:
            self.get_logger().info("Simulation duration reached.")
            return

        # 1. Update Primary Agent
        x, y, z, obj_id = self.agent_primary.get_position_at_time(self.sim_time)
        self.publish_pose(self.pub_primary_pose, x, y, z, "agent_primary")
        
        if obj_id != self.last_obj_id:
            msg = String()
            msg.data = obj_id if obj_id else ""
            self.pub_current_obj.publish(msg)
            self.last_obj_id = obj_id

        # 2. Update Secondary Agent
        x2, y2, z2, _ = self.agent_secondary.get_position_at_time(self.sim_time)
        self.publish_pose(self.pub_secondary_pose, x2, y2, z2, "agent_secondary")
        
        self.sim_time += 0.1

    def publish_pose(self, publisher, x, y, z, frame_id):
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "world"
        msg.pose.position.x = float(x)
        msg.pose.position.y = float(y)
        msg.pose.position.z = float(z)
        msg.pose.orientation.w = 1.0
        publisher.publish(msg)

    def export_callback(self, request, response):
        self.export_csvs()
        response.success = True
        response.message = "Trajectories exported to eval/ground_truth/"
        return response

    def export_csvs(self):
        seed = self.get_parameter('primary_seed').value
        self.agent_primary.export_csv(self.duration, 0.1, f"eval/ground_truth/trajectory_primary_seed{seed}.csv")
        self.agent_secondary.export_csv(self.duration, 0.1, f"eval/ground_truth/trajectory_secondary.csv")
        self.get_logger().info("CSV trajectories exported.")

def main(args=None):
    rclpy.init(args=args)
    node = AgentSimNode()
    
    # Export on shutdown
    def signal_handler(sig, frame):
        node.export_csvs()
        rclpy.shutdown()
        
    signal.signal(signal.SIGINT, signal_handler); signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        # Final export attempt
        try:
            node.export_csvs()
        except:
            pass
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()
