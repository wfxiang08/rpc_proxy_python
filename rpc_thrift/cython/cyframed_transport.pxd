from rpc_thrift.cython.cybase cimport CyTransportBase, TCyBuffer

cdef class TCyFramedTransport(CyTransportBase):
    '''
        用在Client端，工作模式:
            readMessageBegin
                transport#read_frame_2_buff

            其他情况下:
                transport#读取buffer

    '''
    cdef:
        public object trans
        TCyBuffer rbuf, rframe_buf, wframe_buf
        float lastAccessTime
        float maxIdleTime

    cdef _write_rframe_buffer(self, const char *data, int sz)
    cdef read_frame_2_buff(self)
    cdef _flush_frame_buff(self, buff1)
    cdef int read_trans(self, int sz, char *out)



