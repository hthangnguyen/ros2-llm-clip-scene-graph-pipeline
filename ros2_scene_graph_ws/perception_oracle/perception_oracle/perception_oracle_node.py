import rclpy
from rclpy.node import Node
import yaml
import os
import numpy as np

# Custom messages
from scene_graph_msgs.msg import ObjectEmbeddings

# Utilities
from .clip_utils import CLIPEncoder

class PerceptionOracleNode(Node):
    def __init__(self):
        super().__init__('perception_oracle_node')
        
        # Parameters
        self.declare_parameter('scene_config_path', 'config/scene_config.yaml')
        config_path = self.get_parameter('scene_config_path').get_parameter_value().string_value
        
        if not os.path.isabs(config_path):
            config_path = os.path.abspath(config_path)
            
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        self.scene_objects = config['scene']['objects'] + config['scene']['near_miss_objects']
        
        # Initialize CLIP
        self.get_logger().info("Initializing CLIP model (this may take a moment)...")
        self.encoder = CLIPEncoder()
        self.embedding_dim = self.encoder.get_embedding_dim()
        
        # Pre-calculate embeddings for all static objects
        self.get_logger().info(f"Pre-calculating embeddings for {len(self.scene_objects)} objects...")
        self.object_ids = []
        self.embeddings_matrix = []
        
        for obj in self.scene_objects:
            emb = self.encoder.get_text_embedding(obj['label'])
            self.object_ids.append(obj['id'])
            self.embeddings_matrix.append(emb)
            
        self.embeddings_matrix = np.array(self.embeddings_matrix).astype(np.float32)
        
        # Publisher
        self.pub_embeddings = self.create_publisher(ObjectEmbeddings, '/perception/objects', 10)
        
        # Timer (1 Hz - Perception Oracle doesn't need to be fast)
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.get_logger().info("Perception Oracle Node started.")

    def timer_callback(self):
        msg = ObjectEmbeddings()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.object_ids = self.object_ids
        
        # Flatten the (N, 512) matrix into a 1D array for the ROS message
        msg.embeddings_flat = self.embeddings_matrix.flatten().tolist()
        
        self.pub_embeddings.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = PerceptionOracleNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
