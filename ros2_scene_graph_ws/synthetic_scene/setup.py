from setuptools import setup

package_name = 'synthetic_scene'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='aidev1',
    maintainer_email='aidev1@research.com',
    description='Synthetic scene generator for ROS2',
    license='TODO: License declaration',
    # Removed tests_require as it is deprecated in setuptools 82+
    entry_points={
        'console_scripts': [
            'synthetic_scene_node = synthetic_scene.synthetic_scene_node:main',
        ],
    },
)
