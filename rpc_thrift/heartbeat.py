# -*- coding: utf-8 -*-
from __future__ import absolute_import

from rpc_thrift.cython.cybinary_protocol import TCyBinaryProtocol
from rpc_thrift.cython.cymemory_transport import TCyMemoryBuffer

from rpc_thrift import MESSAGE_TYPE_STOP


def new_rpc_exit_message():
    buf = TCyMemoryBuffer()
    protocol = TCyBinaryProtocol(buf)

    protocol.writeMessageBegin("worker_shutdonw", MESSAGE_TYPE_STOP, 0)
    protocol.writeMessageEnd()
    return buf
