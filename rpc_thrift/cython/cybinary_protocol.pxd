cimport rpc_thrift.cython.cybase
from rpc_thrift.cython.cybase cimport CyTransportBase, TCyBuffer
from cpython cimport bool
from libc.stdint cimport int16_t, int32_t, int64_t

ctypedef enum TType:
    T_STOP = 0,
    T_VOID = 1,
    T_BOOL = 2,
    T_BYTE = 3,
    T_I08 = 3,
    T_I16 = 6,
    T_I32 = 8,
    T_U64 = 9,
    T_I64 = 10,
    T_DOUBLE = 4,
    T_STRING = 11,
    T_UTF7 = 11,
    T_NARY = 11
    T_STRUCT = 12,
    T_MAP = 13,
    T_SET = 14,
    T_LIST = 15,
    T_UTF8 = 16,
    T_UTF16 = 17

cdef class TCyBinaryProtocol(object):
    cdef:
        public CyTransportBase trans
        bool strict_read
        bool strict_write
        str  service

    cpdef readMessageBegin(self)
    cpdef writeMessageBegin(self, name, TType ttype, int32_t seqid)