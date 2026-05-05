from setuptools import setup

package_name = 'scene_graph_builder'

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
    description='Scene Graph Builder for ROS2',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'scene_graph_builder_node = scene_graph_builder.scene_graph_builder_node:main',
        ],
    },
)
