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
        read_trans(self, trans, int sz, char *out)


cdef class CyTransportBase(object):
    cdef c_read(self, int sz, char* out)
    cdef c_write(self, char* data, int sz)
    cdef c_flush(self)

    cdef get_string(self, int sz)

