# -*- coding: utf-8 -*-


import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from setuptools.extension import Extension

requirements = [
    'gevent>=1.0',
    'rpc_thrift==0.9.9',
    'colorama>=0.3.3',
    "Cython==0.23.2"
]
if sys.version_info < (2, 7):
    requirements.append('argparse')

from distutils.core import setup
from Cython.Distutils import build_ext

ext_modules = []
files = ["cybase", "cybinary_protocol", "cyframed_transport", "cymemory_transport", "cyframed_transport_ex"]
for f in files:
    ext_modules.append(Extension("rpc_thrift.cython.%s" % f, ["rpc_thrift/cython/cyframed_transport.pxd",
                                                              "rpc_thrift/cython/cyframed_transport_ex.pxd",
                                                              "rpc_thrift/cython/cymemory_transport.pxd",
                                                              "rpc_thrift/cython/cybase.pxd",
                                                              "rpc_thrift/cython/%s.pyx" % f]))


setup(
    name='rpc_proxy',
    version="2.0.9",
    description='rpc_proxy is a flexible RPC based on thrift.',
    author="wangfei",
    author_email="wfxiang08@gmail.com",
    url='https://github.com/wfxiang08/rpc_proxy_python',
    packages=['rpc_thrift', 'rpc_thrift.services', 'rpc_thrift.log_utils', 'rpc_thrift.cython'],
    zip_safe=False,
    license='MIT',
    cmdclass = {'build_ext': build_ext},
    ext_modules=ext_modules,
)