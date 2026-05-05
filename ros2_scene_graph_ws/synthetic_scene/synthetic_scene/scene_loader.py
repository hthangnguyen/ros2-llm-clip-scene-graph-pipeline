import yaml
import os

def load_scene(yaml_path: str) -> dict:
    """Load and validate scene_config.yaml.
    Returns dict with keys: room_dimensions, objects, near_miss_objects, tasks, camera, agents.
    Raises ValueError if object count != 20.
    Raises ValueError if any required field is missing from any object.
    """
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Scene config not found at {yaml_path}")

    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)

    scene = config.get('scene', {})
    
    # Required top-level keys
    required_keys = ['room_dimensions', 'objects', 'near_miss_objects', 'tasks', 'camera']
    for key in required_keys:
        if key not in scene:
            raise ValueError(f"Missing required top-level key in 'scene': {key}")
    
    if 'agents' not in config:
        raise ValueError("Missing 'agents' in config")

    # Validate object count
    objects = scene['objects']
    if len(objects) != 20:
        raise ValueError(f"Expected exactly 20 objects, found {len(objects)}")

    # Validate individual objects
    required_obj_fields = ['id', 'label', 'position', 'size', 'color_rgb', 'task_relevant']
    for i, obj in enumerate(objects):
        for field in required_obj_fields:
            if field not in obj:
                raise ValueError(f"Object {i} ({obj.get('id', 'unknown')}) missing required field: {field}")
        
        # Validate data types for position, size, color
        for field in ['position', 'size', 'color_rgb']:
            if not isinstance(obj[field], (list, tuple)) or len(obj[field]) != 3:
                raise ValueError(f"Object {obj['id']} field '{field}' must be a list of 3 numbers")

    return {
        'room_dimensions': scene['room_dimensions'],
        'objects': objects,
        'near_miss_objects': scene['near_miss_objects'],
        'tasks': scene['tasks'],
        'camera': scene['camera'],
        'agents': config['agents']
    }