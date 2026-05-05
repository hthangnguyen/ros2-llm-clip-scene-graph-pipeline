import numpy as np
import csv
import os

class AgentPath:
    def __init__(self, agent_config: dict, scene_objects: list, rng_seed: int):
        self.config = agent_config
        # map objects by ID for quick lookup
        self.objects = {obj['id']: obj for obj in scene_objects}
        self.rng = np.random.default_rng(rng_seed)
        
        self.speed = agent_config['speed_mps']
        self.mode = agent_config['path_mode']
        self.start_pos = np.array(agent_config['start_position'])
        self.waypoints = agent_config['waypoints']
        
        # Internal state for trajectory calculation
        self.segments = [] # List of (start_pos, end_pos, duration, target_obj_id)
        self._build_trajectory()

    def _build_trajectory(self):
        """Pre-calculate path segments and their durations."""
        current_pos = self.start_pos
        
        # If stochastic, we'd normally sample at runtime, 
        # but for this utility we will pre-generate a sequence.
        if self.mode == 'stochastic':
            # Simplified: pick 20 random waypoints based on probabilities
            probs = [w.get('probability', 1.0) for w in self.waypoints]
            probs = np.array(probs) / sum(probs)
            sequence = self.rng.choice(self.waypoints, size=20, p=probs)
        else:
            # Deterministic: use waypoints in order
            sequence = self.waypoints

        total_time = 0.0
        for wp in sequence:
            target_obj = self.objects.get(wp['object_id'])
            if not target_obj: continue
            
            target_pos = np.array(target_obj['position'])
            dist = np.linalg.norm(target_pos - current_pos)
            duration = dist / self.speed
            
            # Add travel segment
            if duration > 0:
                self.segments.append({
                    'start_t': total_time,
                    'end_t': total_time + duration,
                    'start_p': current_pos.copy(),
                    'end_p': target_pos.copy(),
                    'obj_id': None # Moving
                })
                total_time += duration
            
            # Add dwell segment
            dwell = wp.get('dwell_sec', 0.0)
            if dwell > 0:
                self.segments.append({
                    'start_t': total_time,
                    'end_t': total_time + dwell,
                    'start_p': target_pos.copy(),
                    'end_p': target_pos.copy(),
                    'obj_id': wp['object_id']
                })
                total_time += dwell
            
            current_pos = target_pos

    def get_position_at_time(self, t: float) -> tuple:
        """Returns (x, y, z, current_object_id) at simulation time t."""
        for seg in self.segments:
            if seg['start_t'] <= t <= seg['end_t']:
                if seg['obj_id'] is not None:
                    return (*seg['end_p'], seg['obj_id'])
                
                # Interpolate travel
                frac = (t - seg['start_t']) / (seg['end_t'] - seg['start_t'])
                pos = seg['start_p'] + frac * (seg['end_p'] - seg['start_p'])
                return (*pos, None)
        
        # If beyond duration, return last position
        if self.segments:
            return (*self.segments[-1]['end_p'], self.segments[-1]['obj_id'])
        return (*self.start_pos, None)

    def export_csv(self, duration_sec: float, dt: float, filepath: str):
        """Sample trajectory at dt intervals and write to CSV."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp_sec', 'x', 'y', 'z', 'current_object_id', 'speed_mps'])
            for t in np.arange(0, duration_sec, dt):
                x, y, z, obj_id = self.get_position_at_time(t)
                writer.writerow([round(t, 2), round(x, 3), round(y, 3), round(z, 3), obj_id, self.speed])
