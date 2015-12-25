cimport rpc_thrift.cython.cybase
from rpc_thrift.cython.cybase cimport CyTransportBase, TCyBuffer


cdef class TCyFramedTransportEx(CyTransportBase):
    cdef:
        public object trans
        TCyBuffer rbuf

    cdef read_trans(self, int sz, char* out)

    # 用于服务端(Worker一次读取一个Frame, 然后再交给外部的代码去处理整个Frame
    # 如果read_frame出现异常，那么: 结束读取操作, 但是写回操作继续;
    cpdef read_frame(self)

    # 用于服务端(Worker一次将数据写回给Client)，写回操作异常那么整个读写都结束，否则
    cpdef flush_frame_buff(self, buf)