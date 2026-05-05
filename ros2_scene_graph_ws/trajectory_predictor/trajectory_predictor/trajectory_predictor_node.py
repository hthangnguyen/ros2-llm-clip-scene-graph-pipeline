import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from scene_graph_msgs.msg import SceneGraph
import numpy as np
import scipy.linalg
import os

from .ctmc_utils import CTMCModel
from .llm_utils import LLMInterface

class TrajectoryPredictorNode(Node):
    def __init__(self):
        super().__init__('trajectory_predictor_node')
        
        # Initialize components
        self.llm = LLMInterface()
        self.ctmc = None
        
        # State
        self.current_obj_id = None
        self.current_pos = None
        self.object_map = {} # id -> label
        self.positions = None
        self.ids = []
        
        # Subscribers
        self.sub_graph = self.create_subscription(SceneGraph, '/scene_graph', self.graph_callback, 10)
        self.sub_pose = self.create_subscription(PoseStamped, '/agent_primary/pose', self.pose_callback, 10)
        
        # Publisher
        self.pub_prediction = self.create_publisher(String, '/agent_primary/prediction', 10)
        
        # Timer (0.5 Hz for LLM-heavy task)
        self.timer = self.create_timer(2.0, self.timer_callback)
        self.get_logger().info("Trajectory Predictor Node started.")

    def graph_callback(self, msg):
        if self.ctmc is not None:
            return
            
        # Initialize CTMC once graph is received
        self.ids = msg.object_ids
        self.object_map = dict(zip(msg.object_ids, msg.object_labels))
        self.positions = np.array([[obj.x, obj.y, obj.z] for obj in msg.objects])
        
        self.ctmc = CTMCModel(len(self.ids))
        self.get_logger().info(f"Initialized CTMC with {len(self.ids)} states.")

    def pose_callback(self, msg):
        self.current_pos = np.array([msg.pose.position.x, msg.pose.position.y, msg.pose.position.z])

    def timer_callback(self):
        if self.ctmc is None or self.current_pos is None:
            return

        # 1. Identify current state (nearest object)
        dists = np.linalg.norm(self.positions - self.current_pos, axis=1)
        current_idx = np.argmin(dists)
        current_id = self.ids[current_idx]
        current_label = self.object_map[current_id]

        # 2. Get candidate destinations (nearest 10 states)
        # Exclude self
        dists_copy = dists.copy()
        dists_copy[current_idx] = 1e9
        
        # EXPANDED CANDIDATES TO 10
        candidates_idx = np.argsort(dists_copy)[:10]
        candidate_labels = [self.object_map[self.ids[i]] for i in candidates_idx]
        candidate_dists = [dists[i] for i in candidates_idx]

        # 3. Get LLM Rankings
        scores = self.llm.rank_next_objects(current_label, candidate_labels)
        
        # 4. Update Transition Rates (Q matrix)
        # Rate = Score / Distance
        rates = []
        for score, dist in zip(scores, candidate_dists):
            rates.append(score / (dist + 0.1))
            
        self.ctmc.update_rates(current_idx, candidates_idx, rates)

        # 5. Compute Prediction (Matrix Exponential)
        dt = 5.0 # Predict 5 seconds ahead
        probs = self.ctmc.predict_next_state(current_idx, dt)
        
        # Select best next state (excluding current)
        probs[current_idx] = 0.0
        next_idx = np.argmax(probs)
        next_id = self.ids[next_idx]
        
        # 6. Publish
        msg = String()
        msg.data = f"Current: {current_id} | Predicted Next: {next_id}"
        self.pub_prediction.publish(msg)
        self.get_logger().info(f"Prediction: {msg.data}")

def main(args=None):
    import rclpy
    rclpy.init(args=args)
    node = TrajectoryPredictorNode()
    try:
        rclpy.spin(node)
    except Exception:
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
