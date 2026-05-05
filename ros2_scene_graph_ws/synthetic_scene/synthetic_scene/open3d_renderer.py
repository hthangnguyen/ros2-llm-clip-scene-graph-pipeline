import open3d as o3d
import numpy as np
import math

class SceneRenderer:
    def __init__(self, scene: dict, image_width: int, image_height: int, fov_deg: float):
        """Initialize Open3D OffscreenRenderer. Create box geometry for each object
        and near_miss_object using their position and size. Color each box using color_rgb."""
        self.width = image_width
        self.height = image_height
        self.fov = fov_deg

        # Initialize OffscreenRenderer
        self.renderer = o3d.visualization.rendering.OffscreenRenderer(self.width, self.height)
        self.scene = self.renderer.scene
        self.scene.set_background([0.1, 0.1, 0.1, 1.0])  # Dark background

        # Create materials
        self.mat = o3d.visualization.rendering.MaterialRecord()
        self.mat.shader = "defaultLit"

        # Add objects to the scene
        all_objects = scene['objects'] + scene['near_miss_objects']
        for obj in all_objects:
            # Create box mesh
            # Open3D create_box creates a box with min corner at [0,0,0]
            # We need to center it at the position and scale by size
            size = obj['size']
            pos = obj['position']
            color = obj['color_rgb']

            mesh = o3d.geometry.TriangleMesh.create_box(width=size[0], height=size[1], depth=size[2])
            
            # Translate so that the center is at [0,0,0] then move to pos
            # Actually, standard convention in our config is 'position' is the center
            # create_box creates from [0,0,0] to [size]
            mesh.translate([-size[0]/2, -size[1]/2, -size[2]/2])
            mesh.translate(pos)
            mesh.paint_uniform_color(color)
            mesh.compute_vertex_normals()

            self.scene.add_geometry(obj['id'], mesh, self.mat)

        # Setup camera intrinsics
        # f = (width / 2) / tan(fov / 2)
        f = (self.width / 2.0) / math.tan(math.radians(self.fov) / 2.0)
        self.intrinsics = {
            'fx': f, 'fy': f,
            'cx': self.width / 2.0,
            'cy': self.height / 2.0,
            'width': self.width,
            'height': self.height
        }

    def render(self, camera_position: list, look_at: list) -> tuple:
        """Render scene from given camera pose.
        Returns: (rgb_image_np, depth_image_np)
          rgb_image_np: np.ndarray shape (H, W, 3) dtype uint8
          depth_image_np: np.ndarray shape (H, W) dtype float32, values in meters
        """
        # Set camera
        up = [0, 0, 1]  # Z-up world frame
        self.renderer.setup_camera(self.fov, look_at, camera_position, up)

        # Render
        rgb_image = self.renderer.render_to_image()
        depth_image = self.renderer.render_to_depth_image(z_in_view_space=True)

        return np.asarray(rgb_image), np.asarray(depth_image)

    def get_camera_intrinsics(self) -> dict:
        """Returns dict with keys: fx, fy, cx, cy, width, height"""
        return self.intrinsics
