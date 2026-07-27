"""
Setuptools entry for diy_nav_slam_compare.

Besides the default resource / package.xml, this installs the launch,
config and scripts directories into share/.

The console_scripts entry currently exposes only a placeholder CLI
(slam_compare_cli), which will be replaced by real comparison tools
in later stages.
"""

import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'diy_nav_slam_compare'


def _files_in(directory, pattern='*'):
    """Collect files under `directory` matching `pattern`."""
    if not os.path.isdir(directory):
        return []
    return [f for f in glob(os.path.join(directory, pattern)) if os.path.isfile(f)]


setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        # ament index 注册
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        # package.xml
        ('share/' + package_name, ['package.xml']),
        # launch 文件
        (os.path.join('share', package_name, 'launch'),
            _files_in('launch', '*.launch.py') + _files_in('launch', '*.yaml')),
        # 配置文件
        (os.path.join('share', package_name, 'config'),
            _files_in('config', '*.yaml') + _files_in('config', '*.lua')),
        # 辅助脚本（也可通过 lib/ 安装，这里放到 share 便于查阅）
        (os.path.join('share', package_name, 'scripts'),
            _files_in('scripts')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='czm',
    maintainer_email='czm@example.com',
    description='SLAM comparison utilities (SLAM Toolbox vs Cartographer) for diy_nav_bot.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            # 骨架阶段的占位 CLI；后续阶段会新增比较节点入口
            'slam_compare_cli = diy_nav_slam_compare.cli:main',
        ],
    },
)
