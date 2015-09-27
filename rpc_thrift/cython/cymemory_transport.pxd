cimport rpc_thrift.cython.cybase
from rpc_thrift.cython.cybase cimport CyTransportBase, TCyBuffer

cdef class TCyMemoryBuffer(CyTransportBase):
    cdef TCyBuffer buf
    cdef _getvalue(self)
    cdef _setvalue(self, int sz, const char *value)