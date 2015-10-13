from libc.stdlib cimport malloc, free
from libc.string cimport memcpy
from libc.stdint cimport int32_t



from rpc_thrift.cython.cybase cimport (
    TCyBuffer,
    CyTransportBase,
    DEFAULT_BUFFER,
    STACK_STRING_LEN
)

cimport rpc_thrift.cython.cymemory_transport
from rpc_thrift.cython.cymemory_transport cimport TCyMemoryBuffer

from thrift.transport.TTransport import TTransportException
# from rpc_thrift.cython.cymemory_transport import TCyMemoryBuffer


cdef extern from "./endian_port.h":
    int32_t be32toh(int32_t n)
    int32_t htobe32(int32_t n)


cdef class TCyFramedTransport(CyTransportBase):

    def __init__(self, trans, int buf_size=DEFAULT_BUFFER):
        self.trans = trans # Python对象

        # 负责和transport进行读的buffer操作
        self.rbuf = TCyBuffer(buf_size)

        # 负责对Client的Frame的读写操作
        self.rframe_buf = TCyBuffer(buf_size)

        self.wframe_buf = TCyBuffer(buf_size)
        self.wframe_buf.write(4, "1234") # 占位

    cdef read_trans(self, int sz, char *out):
        cdef int i = self.rbuf.read_trans(self.trans, sz, out)
        if i == -1:
            raise TTransportException(TTransportException.END_OF_FILE,
                                      "End of file reading from transport")
        elif i == -2:
            raise MemoryError("grow buffer fail")

    cdef write_rframe_buffer(self, const char *data, int sz):
        cdef int r = self.rframe_buf.write(sz, data)
        if r == -1:
            raise MemoryError("Write to buffer error")

    cdef c_read(self, int sz, char *out):
        if sz <= 0:
            return 0

        while self.rframe_buf.data_size < sz:
            self._read_frame_internal()

        memcpy(out, self.rframe_buf.buf + self.rframe_buf.cur, sz)
        self.rframe_buf.cur += sz
        self.rframe_buf.data_size -= sz

        return sz

    cdef c_write(self, const char *data, int sz):
        cdef int r = self.wframe_buf.write(sz, data)
        if r == -1:
            raise MemoryError("Write to buffer error")

    cdef _read_frame_internal(self):
        cdef:
            char frame_len[4]
            char stack_frame[STACK_STRING_LEN]
            char *dy_frame
            int32_t frame_size

        # 读取一个新的frame_size
        self.read_trans(4, frame_len)
        frame_size = be32toh((<int32_t*>frame_len)[0])

        if frame_size <= 0:
            raise TTransportException("No frame.", TTransportException.UNKNOWN)

        if frame_size <= STACK_STRING_LEN:
            # 读取frame_size 数据，然后写入: read buffer
            self.read_trans(frame_size, stack_frame)
            self.write_rframe_buffer(stack_frame, frame_size)
        else:
            dy_frame = <char*>malloc(frame_size)
            try:
                self.read_trans(frame_size, dy_frame)
                self.write_rframe_buffer(dy_frame, frame_size)
            finally:
                free(dy_frame)


    cpdef read_frame(self):
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

    def flush(self):
        """
            flush和c_flush等价，并且多次重复调用没有副作用
        """
        self.c_flush()

    cdef c_flush(self):
        cdef:
            bytes data
            char *size_str
            int32_t size

        # self.wframe_buf.cur 似乎只有在读操作中才会改变，其他情况下不变，默认为0

        if self.wframe_buf.data_size > 4:
            # 只有存在有效的数据，才flush; 防止重复调用
            try:
                if not self.isOpen():
                    self.open()
                size = htobe32(self.wframe_buf.data_size - 4)
                memcpy(self.wframe_buf.buf, &size, 4)

                data = self.wframe_buf.buf[:self.wframe_buf.data_size]

                # size_str = <char*>(&size)
                self.trans.write(data)
                self.trans.flush()

                self.wframe_buf.clean()
                self.wframe_buf.write(4, "1234") # 占位
            except:
                # 如果遇到异常，则关闭transaction
                self.close()
                self.clean()
                raise


    cdef _flush_frame_buff(self, buff1):
        cdef:
            TCyMemoryBuffer buff
        try:

            buff = buff1
            if not self.isOpen():
                self.open()

            frame = buff.get_frame_value()

            self.trans.write(frame)
            self.trans.flush()
        except:
            # 如果遇到异常，则关闭transaction
            self.close()
            self.clean()
            raise

    def flush_frame_buff(self, buf):
        self._flush_frame_buff(buf)

    def read(self, int sz):
        try:
            return self.get_string(sz)
        except:
            # 如果遇到异常，则关闭transaction
            self.close()
            self.clean()
            raise

    def write(self, bytes data):
        cdef int sz = len(data)
        self.c_write(data, sz)




    def isOpen(self):
        return self.trans.isOpen()

    def open(self):
        return self.trans.open()

    def close(self):
        return self.trans.close()

    def clean(self):
        self.rbuf.clean()
        self.rframe_buf.clean()

        self.wframe_buf.clean()
        self.wframe_buf.write(4, "1234") # 占位


class TCyFramedTransportFactory(object):
    def get_transport(self, trans):
        return TCyFramedTransport(trans)
