from setuptools import setup

package_name = 'perception_oracle'

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
    description='Perception Oracle for ROS2 scene graph',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'perception_oracle_node = perception_oracle.perception_oracle_node:main',
        ],
    },
)
