cimport rpc_thrift.cython.cybase
from rpc_thrift.cython.cybase cimport CyTransportBase, TCyBuffer
from cpython cimport bool
from libc.stdint cimport int16_t, int32_t, int64_t

cdef class TCyFramedTransport(CyTransportBase):
    cdef:
        public object trans
        TCyBuffer rbuf, rframe_buf, wframe_buf
        float lastAccessTime
        float maxIdleTime

    cdef write_rframe_buffer(self, const char *data, int sz)
    cdef _read_frame_internal(self)
    cdef _flush_frame_buff(self, buff1)
    cdef read_trans(self, int sz, char *out)

