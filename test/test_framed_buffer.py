# -*- coding:utf-8 -*-
from __future__ import  absolute_import
from rpc_thrift.cython.cyframed_transport_ex import TCyFramedTransportEx

from rpc_thrift.cython.cymemory_transport import TCyMemoryBuffer
from rpc_thrift.cython.cyframed_transport import TCyFramedTransport

from rpc_thrift.transport import TMemoryBuffer


# 这个相对路径如何处理呢?
from unittest import TestCase


class FramedBufferTest(TestCase):

    def setUp(self):
        super(FramedBufferTest, self).setUp()
        print ""


    def tearDown(self):
        super(FramedBufferTest, self).tearDown()

    def test_write_flush(self):
        """
            py.test test/test_framed_buffer.py::FramedBufferTest::test_write_flush -s
        """
        buf = TMemoryBuffer()
        transport = TCyFramedTransport(buf)
        transport.write("abcdef")
        transport.flush()

        print "Framed Output: ", ["%03d" % ord(i) for i in buf.getvalue()]

        # MemoryBuffer作为FrameBuffer来使用
        buf2 = TCyMemoryBuffer()
        buf2.prepare_4_frame()
        buf2.write("abcdef")

        buf1 = TMemoryBuffer()
        tran1 = TCyFramedTransportEx(buf1)
        tran1.flush_frame_buff(buf2)

        print "Framed Output: ", ["%03d" % ord(i) for i in buf1.getvalue()]

        buf1.reset()
        tran1 = TCyFramedTransportEx(buf1)

        mem_trans = tran1.read_frame()
        print "ReadFrame: ", mem_trans
        value = mem_trans.getvalue()
        print "Value: ", value,  ["%03d" % ord(i) for i in value]

