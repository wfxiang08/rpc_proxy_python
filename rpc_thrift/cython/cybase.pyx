# 在PyCharm中有警告，如何解除？
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy, memmove, memset


# 自己实现的Buffer, 不使用: cStringIO
cdef class TCyBuffer(object):
    def __cinit__(self, buf_size):

        self.buf = <char*>malloc(buf_size)
        self.buf_size = buf_size

        self.cur = 0
        self.data_size = 0 # 可以继续读取的byte数

    def __dealloc__(self):
        if self.buf != NULL:
            free(self.buf)
            self.buf = NULL

    cdef void move_to_start(self):
        # http://man7.org/linux/man-pages/man3/memmove.3.html
        memmove(self.buf, self.buf + self.cur, self.data_size)
        self.cur = 0

    cdef void clean(self):
        # 底层的数据不变，但是状态reset
        # buf, buf_size不变
        self.cur = 0
        self.data_size = 0

    cdef void reset(self):
        '''
        在读取数据时，cur设置到最开始的位置0
        '''
        self.data_size += self.cur
        self.cur = 0

    cdef void skip_bytes(self, sz):
        if self.data_size >= sz:
            self.cur += sz
            self.data_size -= sz

    # cdef get_value(self):
    #     # 直接返回buffer中的所有的数据
    #     return self.buf[0:(self.data_size + self.cur)]

    cdef int write(self, int sz, const char *value):
        cdef:
            int cap = self.buf_size - self.data_size # 空闲的内存
            int remain = cap - self.cur # 现有数据后，可以写的内存

        if sz <= 0:
            return 0

        if remain < sz: # 整理内存(尽量lazy处理)
            self.move_to_start()

        # recompute remain spaces
        remain = cap - self.cur

        if remain < sz:
            # sz - remain + self.buf_size 新的size的需求
            if self.grow(sz - remain + self.buf_size) != 0:
                return -1

        # 写数据的时候: cur基本不变(除非遇到数据整理)
        memcpy(self.buf + self.cur + self.data_size, value, sz)
        self.data_size += sz

        return sz

    # 返回 0+， 表示正常
    # 返回 -2, 表示内存分配失败
    # 返回 -1, 表示网络断开等错误
    cdef int read_trans(self, trans, int sz, char *out):
        # 如何和python中的对象交互呢?
        cdef int cap, new_data_len

        if sz <= 0:
            return 0

        # buffer中的数据不够
        if self.data_size < sz:
            # buf_size也要调整
            if self.buf_size < sz:
                if self.grow(sz) != 0:
                    return -2  # grow buffer error

            cap = self.buf_size - self.data_size

            new_data = trans.read(cap)
            new_data_len = len(new_data)

            while new_data_len + self.data_size < sz:
                # 数据可能一次不能读取完毕；但是一定会继续等待，直到有新的数据，或者出现连接断开
                more = trans.read(cap - new_data_len)
                more_len = len(more)
                if more_len <= 0:
                    return -1  # end of file error

                new_data += more
                new_data_len += more_len

            if cap - self.cur < new_data_len:
                self.move_to_start()

            memcpy(self.buf + self.cur + self.data_size, <char*>new_data,
                   new_data_len)
            self.data_size += new_data_len

        memcpy(out, self.buf + self.cur, sz)
        self.cur += sz
        self.data_size -= sz

        return sz

    # 返回0, 表示成功；返回-1表示内存分配失败
    cdef int grow(self, int min_size):
        if min_size <= self.buf_size:
            return 0

        # 倍数: ceil(min_size / buf_size)
        cdef int multiples = min_size / self.buf_size
        if min_size % self.buf_size != 0:
            multiples += 1

        cdef int new_size = self.buf_size * multiples
        cdef char *new_buf = <char*>malloc(new_size)
        if new_buf == NULL:
            return -1

        memcpy(new_buf + self.cur, self.buf + self.cur, self.data_size)
        free(self.buf)
        self.buf_size = new_size
        self.buf = new_buf
        return 0


# C实现的Transport的基本接口
cdef class CyTransportBase(object):
    #
    # CyFramedTransport 如何是实现呢?
    # 大部分情况下读取Buffer, 没有数据再从Transport读取数据
    #
    cdef int c_read(self, int sz, char* out):
        pass

    cdef c_write(self, char* data, int sz):
        pass

    cdef c_flush(self):
        pass

    def clean(self):
        pass

    cdef get_string(self, int sz):
        cdef:
            char out[STACK_STRING_LEN]
            char *dy_out

        if sz > STACK_STRING_LEN:
            # 直接分配新的buff, 然后再读取
            dy_out = <char*>malloc(sz)
            try:
                # size为实际读取的size
                size = self.c_read(sz, dy_out)
                return dy_out[:size]
            finally:
                free(dy_out)
        else:
            # 这是什么用法， C数组还能slice
            size = self.c_read(sz, out)
            return out[:size]
