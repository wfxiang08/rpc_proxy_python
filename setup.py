# -*- coding: utf-8 -*-


import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requirements = [
    'gevent>=1.0',
    'thrift==0.9.2',
    'colorama>=0.3.3'
]
if sys.version_info < (2, 7):
    requirements.append('argparse')

from distutils.core import setup
from Cython.Build import cythonize


setup(
    name='rpc_proxy',
    version="0.9.1",
    description='rpc_proxy is a flexible RPC based on thrift.',
    author="wangfei@chunyu.me",
    url='https://git.chunyu.me/infra/rpc_proxy/tree/master/lib',
    packages=['rpc_thrift', 'rpc_thrift.services', 'rpc_thrift.log_utils'],
    zip_safe=False,
    license='MIT',
    ext_modules = cythonize("**/*.pyx"),
)
