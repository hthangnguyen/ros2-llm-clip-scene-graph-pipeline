import numpy as np

def depth_to_pointcloud(depth_np: np.ndarray, intrinsics: dict) -> np.ndarray:
    """Back-project depth image to 3D point cloud.
    intrinsics: dict with fx, fy, cx, cy
    Returns: np.ndarray shape (N, 3) dtype float32, world-frame XYZ points.
    Filters out points where depth == 0 or depth > 20.0 meters.
    """
    height, width = depth_np.shape
    fx = intrinsics['fx']
    fy = intrinsics['fy']
    cx = intrinsics['cx']
    cy = intrinsics['cy']

    # Create pixel grid
    u, v = np.meshgrid(np.arange(width), np.arange(height))
    
    # Flatten everything for vectorization
    u = u.flatten()
    v = v.flatten()
    z = depth_np.flatten()

    # Mask valid depth
    mask = (z > 0) & (z < 20.0)
    u, v, z = u[mask], v[mask], z[mask]

    # Back-project
    # x = (u - cx) * z / fx
    # y = (v - cy) * z / fy
    x = (u - cx) * z / fx
    y = (v - cy) * z / fy
    
    # In Open3D view space: x is right, y is down, z is forward
    # Our world frame convention is Z-up. 
    # For now, we return these as view-space points. 
    # The transformation to world frame is handled by the ROS node using TF.
    points = np.stack([x, y, z], axis=-1).astype(np.float32)
    
    return points
