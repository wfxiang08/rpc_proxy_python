from libc.string cimport memcpy
from libc.stdlib cimport malloc, free
from libc.stdint cimport int32_t
from rpc_thrift.cython.cybase cimport (
    TCyBuffer,
    CyTransportBase,
    DEFAULT_BUFFER,
)

cdef extern from "./endian_port.h":
    int32_t be32toh(int32_t n)
    int32_t htobe32(int32_t n)

def to_bytes(s):
    try:
        return s.encode("utf-8")
    except Exception:
        return s

# 基于内存的Buffer Transport
cdef class TCyMemoryBuffer(CyTransportBase):


    def __init__(self, value=b'', int buf_size=DEFAULT_BUFFER):
        self.buf = TCyBuffer(buf_size)

        if value:
            self.setvalue(value)

    def reset(self):
        self.buf.reset()

    def prepare_4_frame(self):
        self.clean()
        self.buf.write(4, "1234")




    def get_frame_value(self):
        size = htobe32(self.buf.data_size - 4)
        memcpy(self.buf.buf, &size, 4)
        return self.buf.buf[:self.buf.data_size]


    cdef c_read(self, int sz, char* out):
        # 限制读取的参数
        if self.buf.data_size < sz:
            sz = self.buf.data_size

        if sz <= 0:
            out[0] = '\0'
        else:
            memcpy(out, self.buf.buf + self.buf.cur, sz)
            self.buf.cur += sz
            self.buf.data_size -= sz

        return sz

    cdef c_write(self, const char* data, int sz):
        # print "c_write: ", data[:sz]
        cdef int r = self.buf.write(sz, data)
        if r == -1:
            raise MemoryError("Write to memory error")

    cdef _getvalue(self):
        # 读取“剩下”的可读的数据
        cdef char *out
        cdef int size = self.buf.data_size

        if size <= 0:
            return b''

        out = <char*>malloc(size)
        try:
            memcpy(out, self.buf.buf + self.buf.cur, size)
            return out[:size]
        finally:
            free(out)

    cdef _setvalue(self, int sz, const char *value):
        self.buf.clean()
        self.buf.write(sz, value)

    def reset_frame(self):
        # 回到Frame的开始位置
        self.buf.reset()
        self.buf.skip_bytes(4)

    # Transport主要解决读和写的问题
    def read(self, sz):
        return self.get_string(sz)

    def write(self, data):
        data = to_bytes(data)

        cdef int sz = len(data)
        return self.c_write(data, sz)

    def isOpen(self):
        return True

    def open(self):
        pass

    def close(self):
        pass

    def flush(self):
        pass

    def clean(self):
        self.buf.clean()

    def getvalue(self):
        return self._getvalue()

    def setvalue(self, value):
        # value为python  str
        value = to_bytes(value)
        # 类型自动转换: value --> const char*
        self._setvalue(len(value), value)
