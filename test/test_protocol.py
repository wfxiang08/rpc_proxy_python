# -*- coding:utf-8 -*-
from __future__ import  absolute_import

import time

from thrift.protocol.TBinaryProtocol import TBinaryProtocol

from rpc_thrift.cython.cybinary_protocol import TCyBinaryProtocol
from rpc_thrift.cython.cymemory_transport import TCyMemoryBuffer
from rpc_thrift.protocol import TUtf8BinaryProtocol
from rpc_thrift.transport import TMemoryBuffer

# 这个相对路径如何处理呢?
from rpc_thrift.services.ttypes import RpcException
from unittest import TestCase
from demo.ttypes import Location, Locations


class SimpleTest(TestCase):

    def setUp(self):
        super(SimpleTest, self).setUp()
        print ""


    def tearDown(self):
        super(SimpleTest, self).tearDown()

    def test_read_write_locations(self):
        """
            py.test test/test_protocol.py::SimpleTest::test_read_write_locations -s
        """

        loc0 = Location(u"武汉", "湖北", ["名字", u"姓名"])
        self._test_read_write_ok(loc0)

        loc1 = Location(u"武汉", "湖北", ("名字", u"姓名"))
        self._test_read_write_ok(loc1)

        locs = Locations([loc0, loc1], None, [1, 2, 4])
        self._test_read_write_ok(locs)


        locs1 = self.decode_write(locs)
        self.assertEqual(len(locs.locations), len(locs1.locations))
        self.assertEqual(locs.strs, locs1.strs)
        print "locs1 ints: ", locs1.ints


    def _test_read_write_ok(self, obj):
        # cython版本
        buff0 = TCyMemoryBuffer()
        op0 = TCyBinaryProtocol(buff0)
        op0.write_struct(obj)
        value0 = buff0.getvalue()

        # Python版本
        buff1 = TMemoryBuffer()
        op1 = TUtf8BinaryProtocol(buff1)
        obj.write(op1)
        value1 = buff1.get_raw_value()

        self.assertEqual(value1, value0, "write result not the same")


    def decode_write(self, obj):
        buff0 = TCyMemoryBuffer()
        op0 = TCyBinaryProtocol(buff0)
        op0.write_struct(obj)
        value0 = buff0.getvalue()

        buff1 = TCyMemoryBuffer(value0)
        op1 = TCyBinaryProtocol(buff1)
        obj1 = obj.__class__()

        return op1.read_struct(obj1)

    def test_read_write_exception(self):
        """
            测试可行性
            py.test test/test_protocol.py::SimpleTest::test_read_write_exception -s
        """
        ex = RpcException(1, "Hello")

        self._test_read_write_ok(ex)

        total_time = 1
        t = time.time()
        for i in range(total_time):
            buff0 = TCyMemoryBuffer()
            op0 = TCyBinaryProtocol(buff0)
            op0.write_struct(ex)
            value0 = buff0.getvalue()
        t = time.time() - t
        print "T: %.3fms" % (t * 1000)
        print "Value0:", ["%03d" % ord(i) for i in value0]

        buff0 = TCyMemoryBuffer(value0)
        op0 = TCyBinaryProtocol(buff0)
        ex0 = op0.read_struct(RpcException())
        print "Code: ", ex0.code
        print "Msg: ", ex0.msg







        t = time.time()
        for i in range(total_time):
            buff1 = TMemoryBuffer()
            op1 = TBinaryProtocol(buff1)
            ex.write(op1)
            value1 = buff1.get_raw_value()
        t = time.time() - t
        print "T: %.3fms" % (t * 1000)
        print "Value1:", ["%03d" % ord(i) for i in value1]

        self.assertEqual(value1, value0, "write struct test failed")