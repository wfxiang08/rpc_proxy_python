# 定义接口
cdef enum:
    DEFAULT_BUFFER = 4096
    STACK_STRING_LEN = 4096

# 定义了Buffer 和 Transport
cdef class TCyBuffer(object):
    cdef:
        char *buf
        int cur, buf_size, data_size

        void move_to_start(self)
        void clean(self)
        void reset(self)
        void skip_bytes(self, sz)
        int write(self, int sz, const char *value)
        int grow(self, int min_size)

        # 返回 0+， 表示正常
        # 返回 -2, 表示内存分配失败
        # 返回 -1, 表示网络断开等错误
        int read_trans(self, trans, int sz, char *out)


cdef class CyTransportBase(object):
    #
    # CyFramedTransport 如何是实现呢?
    # 大部分情况下读取Buffer, 没有数据再从Transport读取数据，如果遇到异常transport 自动断开，清除状态
    #
    cdef int c_read(self, int sz, char* out)
    cdef c_write(self, char* data, int sz)
    cdef c_flush(self)


    # 底层调用: c_read, 因此也具有状态自恢复的功能
    cdef get_string(self, int sz)

