"""setup.py — diy_nav_slam_compare

Python 软件包安装脚本。除了默认的 resource / package.xml 之外，
还安装 launch/config/scripts 三个资源目录到 share/。

console_scripts 目前提供一个占位 CLI（slam_compare_cli），会在后续阶段
被具体的比较工具替换。
"""

import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'diy_nav_slam_compare'


def _files_in(directory, pattern='*'):
    """收集 directory 下匹配 pattern 的文件；目录不存在或空时返回空列表。"""
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
