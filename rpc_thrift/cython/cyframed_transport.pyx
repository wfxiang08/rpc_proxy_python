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


#
# 用户客户端的同步读写的Transport
# 任何读写错误都会导致transport的close和buffer的clean
#
cdef class TCyFramedTransport(CyTransportBase):

    def __init__(self, trans, int buf_size=DEFAULT_BUFFER, float maxIdleTime=-1):
        self.trans = trans # Python对象

        # 负责和transport进行读的buffer操作
        self.rbuf = TCyBuffer(buf_size)

        # 负责对Client的Frame的读写操作
        self.rframe_buf = TCyBuffer(buf_size)

        self.wframe_buf = TCyBuffer(buf_size)
        self.wframe_buf.write(4, "1234") # 占位
        self.lastAccessTime = time.time() # 上次访问时间
        self.maxIdleTime = maxIdleTime



    cdef int read_trans(self, int sz, char *out):
        # 返回 0+， 表示正常
        # 返回 -2, 表示内存分配失败
        # 返回 -1, 表示网络断开等错误
        cdef int i = self.rbuf.read_trans(self.trans, sz, out)

        if i == -1:
            self.close()
            self.clean()
            raise TTransportException(TTransportException.END_OF_FILE,
                                      "End of file reading from transport")
        elif i == -2:
            self.close()
            self.clean()
            raise MemoryError("grow buffer fail")

        return i

    cdef int _write_rframe_buffer(self, const char *data, int sz):
        """
            将data（完整的一帧数据）中的数据添加到 rframe_buf后面， rframe_buf应该为空
        :param data:
        :param sz:
        :return:
        """
        self.rframe_buf.clean()
        cdef int r = self.rframe_buf.write(sz, data)
        if r == -1:
            self.close()
            self.clean()
            raise MemoryError("Write to buffer error")
        return r

    cdef int c_read(self, int sz, char *out):
        if sz <= 0:
            return 0

        if self.rframe_buf.data_size < sz:
            self.close()
            self.clean()
            raise TTransportException(TTransportException.END_OF_FILE, "Invalid status, data size is under expected")

        memcpy(out, self.rframe_buf.buf + self.rframe_buf.cur, sz)
        self.rframe_buf.cur += sz
        self.rframe_buf.data_size -= sz

        return sz

    cdef c_write(self, const char *data, int sz):
        cdef int r = self.wframe_buf.write(sz, data)
        if r == -1:
            self.close()
            self.clean()
            raise MemoryError("Write to buffer error")


    cpdef read_frame_2_buff(self):
        """
        读取一帧数据到内部buffer中
        :return:
        """
        cdef:
            char frame_len[4]
            char stack_frame[STACK_STRING_LEN]
            char *dy_frame
            int32_t frame_size
        try:
            # 读取一个新的frame_size
            self.read_trans(4, frame_len)
            frame_size = be32toh((<int32_t*>frame_len)[0])

            if frame_size <= 0:
                raise TTransportException(TTransportException.UNKNOWN, "Frame Size Read Error")

            if frame_size <= STACK_STRING_LEN:
                # 读取frame_size 数据，然后写入: read buffer
                self.read_trans(frame_size, stack_frame)
                self._write_rframe_buffer(stack_frame, frame_size)
            else:
                dy_frame = <char*>malloc(frame_size)
                try:
                    self.read_trans(frame_size, dy_frame)
                    self._write_rframe_buffer(dy_frame, frame_size)
                finally:
                    free(dy_frame)
        except:
            self.close()
            self.clean()
            raise

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

                if self.maxIdleTime > 0:
                    now = time.time()
                    # 如果长时间没有访问（例如: 10分钟，则关闭socket, 重启)
                    if now - self.lastAccessTime > self.maxIdleTime:
                        # print "Close Transport...."
                        self.rbuf.clean()
                        self.rframe_buf.clean()
                        self.close()
                        # self.clean()

                    self.lastAccessTime = now
                if not self.isOpen():
                    self.open()

                # print "Size: ", self.wframe_buf.data_size
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

    def read(self, int sz):
        # get_string内部已经处理了异常逻辑
        return self.get_string(sz)

    def write(self, bytes data):
        cdef int sz = len(data)
        self.c_write(data, sz)


    def isOpen(self):
        return self.trans.isOpen()

    def open(self):
        return self.trans.open()

    # 断开连接
    def close(self):
        return self.trans.close()

    # 重置缓存
    # 同时删除: rbuf, rframe_buf, wframe
    def clean(self):
        self.rbuf.clean()
        self.rframe_buf.clean()

        self.wframe_buf.clean()
        self.wframe_buf.write(4, "1234") # 占位



class TCyFramedTransportFactory(object):
    def get_transport(self, trans):
        return TCyFramedTransport(trans)
