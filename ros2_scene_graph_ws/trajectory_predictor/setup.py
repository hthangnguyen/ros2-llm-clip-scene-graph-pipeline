from setuptools import setup

package_name = 'trajectory_predictor'

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
    description='Trajectory Predictor using CTMC and LLM',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'trajectory_predictor_node = trajectory_predictor.trajectory_predictor_node:main',
        ],
    },
)
