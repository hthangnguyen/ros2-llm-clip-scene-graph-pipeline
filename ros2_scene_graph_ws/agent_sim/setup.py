from setuptools import setup
package_name = 'agent_sim'
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
    description='Agent simulation for ROS2 scene graph',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'agent_sim_node = agent_sim.agent_sim_node:main',
        ],
    },
)