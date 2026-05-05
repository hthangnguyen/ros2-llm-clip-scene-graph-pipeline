import rclpy
from rclpy.node import Node
import numpy as np

# Custom messages
from scene_graph_msgs.msg import SceneGraph, SceneObject, ObjectEmbeddings

# Utilities
from .ib_utils import IBClusterer

class SceneGraphBuilderNode(Node):
    def __init__(self):
        super().__init__('scene_graph_builder_node')
        
        # Parameters
        self.declare_parameter('beta', 1.0)
        self.declare_parameter('tau', 0.05)
        
        # Initialize IB
        self.clusterer = IBClusterer(
            beta=self.get_parameter('beta').value,
            tau=self.get_parameter('tau').value
        )
        
        # State
        self.latest_embeddings = {} # map object_id -> embedding (list)
        
        # Subscribers
        self.sub_embeddings = self.create_subscription(
            ObjectEmbeddings, '/perception/objects', self.embeddings_callback, 10)
        
        self.sub_gt = self.create_subscription(
            SceneGraph, '/ground_truth/objects', self.gt_callback, 10)
            
        # Publisher
        self.pub_scene_graph = self.create_publisher(SceneGraph, '/scene_graph', 10)
        
        self.get_logger().info("Scene Graph Builder Node started.")

    def embeddings_callback(self, msg):
        """Store the latest embeddings received from perception."""
        # Reshape the flattened array back to (N, 512)
        # We know CLIP is 512 for ViT-B-32
        dim = 512
        num_objs = len(msg.object_ids)
        matrix = np.array(msg.embeddings_flat).reshape(num_objs, dim)
        
        for i, obj_id in enumerate(msg.object_ids):
            self.latest_embeddings[obj_id] = matrix[i].tolist()

    def gt_callback(self, msg):
        """Triggered by ground truth objects. Merges them with embeddings and publishes."""
        if not self.latest_embeddings:
            self.get_logger().warn("No embeddings received yet, skipping graph update.", throttle_duration_sec=5.0)
            return

        graph_msg = SceneGraph()
        graph_msg.header = msg.header
        
        # In this Oracle phase, we simply match by ID
        for gt_obj in msg.objects:
            new_obj = SceneObject()
            new_obj.object_id = gt_obj.object_id
            new_obj.semantic_label = gt_obj.semantic_label
            new_obj.position_xyz = gt_obj.position_xyz
            new_obj.bbox_min_xyz = gt_obj.bbox_min_xyz
            new_obj.bbox_max_xyz = gt_obj.bbox_max_xyz
            new_obj.is_dynamic = gt_obj.is_dynamic
            new_obj.task_relevance = gt_obj.task_relevance
            
            # Attach the embedding if we have it
            if gt_obj.object_id in self.latest_embeddings:
                new_obj.clip_embedding = self.latest_embeddings[gt_obj.object_id]
            
            # Simplified IB Clustering logic: 
            # In Phase 3, we treat each unique ID as its own cluster for simplicity.
            new_obj.ib_cluster_id = f"cluster_{gt_obj.object_id}"
            
            graph_msg.objects.append(new_obj)
            
        self.pub_scene_graph.publish(graph_msg)

def main(args=None):
    rclpy.init(args=args)
    node = SceneGraphBuilderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
