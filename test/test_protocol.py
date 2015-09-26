# -*- coding:utf-8 -*-
from __future__ import  absolute_import

import os
import sys
import time


# ROOT = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
# if not ROOT in sys.path[:1]:
#     sys.path.insert(0, ROOT)

# 这个相对路径如何处理呢?
from rpc_thrift.services.ttypes import RpcException
from unittest import TestCase

class SimpleTest(TestCase):

    def setUp(self):
        super(SimpleTest, self).setUp()


    def tearDown(self):
        super(SimpleTest, self).tearDown()

    def test_read_write_locations(self):
        """
            py.test test/test_protocol.py::SimpleTest::test_read_write_locations -s
        """
        from demo.ttypes import Location
        # Location

    def test_read_write_exception(self):
        """
            py.test test/test_protocol.py::SimpleTest::test_read_write_exception -s
        """
        print ""
        ex = RpcException(1, "Hello")

        from rpc_thrift.cython.cybinary_protocol import TCyBinaryProtocol
        from rpc_thrift.cython.cymemory_transport import TCyMemoryBuffer

        t = time.time()
        for i in range(10000):
            buff0 = TCyMemoryBuffer()
            op0 = TCyBinaryProtocol(buff0)
            op0.write_struct(ex)
            value0 = buff0.getvalue()
        t = time.time() - t
        print "T: %.3fms" % (t * 1000)
        print "Value0:", ["%03d" % ord(i) for i in value0]


        from rpc_thrift.transport import TMemoryBuffer
        from thrift.protocol.TBinaryProtocol import TBinaryProtocol

        t = time.time()
        for i in range(10000):
            buff1 = TMemoryBuffer()
            op1 = TBinaryProtocol(buff1)
            ex.write(op1)
            value1 = buff1.get_raw_value()
        t = time.time() - t
        print "T: %.3fms" % (t * 1000)
        print "Value1:", ["%03d" % ord(i) for i in value1]

        # self.assertEqual(value1, value0, "write struct test failed")