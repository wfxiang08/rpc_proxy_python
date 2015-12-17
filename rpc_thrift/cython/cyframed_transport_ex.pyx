from libc.stdlib cimport malloc, free
from libc.string cimport memcpy
from libc.stdint cimport int32_t
import time

from rpc_thrift.cython.cybase cimport (
    TCyBuffer,
    CyTransportBase,
    DEFAULT_BUFFER,
    STACK_STRING_LEN
)

cimport rpc_thrift.cython.cymemory_transport
from rpc_thrift.cython.cymemory_transport cimport TCyMemoryBuffer

from thrift.transport.TTransport import TTransportException

cdef extern from "./endian_port.h":
    int32_t be32toh(int32_t n)
    int32_t htobe32(int32_t n)


cdef class TCyFramedTransportEx(CyTransportBase):

    def __init__(self, trans, int buf_size=DEFAULT_BUFFER):
        self.trans = trans # Python对象 socket
        self.rbuf = TCyBuffer(buf_size)

    def isOpen(self):
        return self.trans.isOpen()

    def open(self):
        self.rbuf.clean()
        return self.trans.open()

    # 断开连接
    def close(self):
        self.rbuf.clean()
        return self.trans.close()

    def clean(self):
        pass

    cdef c_read(self, int sz, char* out):
        raise TTransportException(TTransportException.UNKNOWN, "Method not allowed")
    cdef c_write(self, char* data, int sz):
        raise TTransportException(TTransportException.UNKNOWN, "Method not allowed")
    cdef c_flush(self):
        raise TTransportException(TTransportException.UNKNOWN, "Method not allowed")
    cdef get_string(self, int sz):
        raise TTransportException(TTransportException.UNKNOWN, "Method not allowed")


    #-------------------------------------------------------------------------------------------------------------------
    cpdef read_trans(self, int sz, char* out):
        # 从trans中读取数据
        cdef int i = self.rbuf.read_trans(self.trans, sz, out)

        if i == -1:
            raise TTransportException(TTransportException.END_OF_FILE,
                                      "End of file reading from transport")
        elif i == -2:
            raise MemoryError("grow buffer fail")

    cpdef read_frame(self):
        # 用于服务端(Worker一次读取一个Frame, 然后再交给外部的代码去处理整个Frame
        # 如果read_frame出现异常，那么: 结束读取操作, 但是写回操作继续;
        # 如何读取一帧数据，并且以 TCyMemoryBuffer 形式返回
        cdef:
            char frame_len[4]
            int32_t frame_size
            TCyMemoryBuffer buff

        # 读取一个新的frame_size
        self.read_trans(4, frame_len)
        frame_size = be32toh((<int32_t*>frame_len)[0])

        if frame_size <= 0:
            raise TTransportException("No frame.", TTransportException.UNKNOWN)

        buffer = TCyMemoryBuffer(buf_size=4 + frame_size)
        buffer.c_write(frame_len, 4)
        self.read_trans(frame_size, buffer.buf.buf + 4)
        buffer.buf.data_size = 4 + frame_size

        return buffer

    # ------------------------------------------------------------------------------------------------------------------
    # 用于服务端(Worker一次将数据写回给Client)，写回操作异常那么整个读写都结束，否则
    cpdef flush_frame_buff(self, buff):
        try:

            if not self.isOpen():
                raise TTransportException(TTransportException.NOT_OPEN, "Transport Closed")

            frame = buff.get_frame_value()
            self.trans.write(frame)
            self.trans.flush()
        except:
            # 写失败了，则最终关闭，并且清理buffer
            self.close()
            raise
