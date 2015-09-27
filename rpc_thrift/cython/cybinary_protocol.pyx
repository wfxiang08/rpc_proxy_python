from libc.stdlib cimport free, malloc
from libc.stdint cimport int16_t, int32_t, int64_t
from cpython cimport bool

from rpc_thrift.cython.cybase cimport CyTransportBase, STACK_STRING_LEN

from rpc_thrift.cython import TDecodeException
from time import time

cdef extern from "endian_port.h":
    int16_t htobe16(int16_t n)
    int32_t htobe32(int32_t n)
    int64_t htobe64(int64_t n)
    int16_t be16toh(int16_t n)
    int32_t be32toh(int32_t n)
    int64_t be64toh(int64_t n)

DEF VERSION_MASK = -65536
DEF VERSION_1 = -2147418112
DEF TYPE_MASK = 0x000000ff

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


class ProtocolError(Exception):
    pass


cdef inline char read_i08(CyTransportBase buf) except? -1:
    cdef char data = 0
    buf.c_read(1, &data)
    return data


cdef inline int16_t read_i16(CyTransportBase buf) except? -1:
    cdef char data[2]
    buf.c_read(2, data)
    return be16toh((<int16_t*>data)[0])


cdef inline int32_t read_i32(CyTransportBase buf) except? -1:
    cdef char data[4]
    buf.c_read(4, data)
    return be32toh((<int32_t*>data)[0])


cdef inline int64_t read_i64(CyTransportBase buf) except? -1:
    cdef char data[8]
    buf.c_read(8, data)
    return be64toh((<int64_t*>data)[0])


cdef inline int write_i08(CyTransportBase buf, char val) except -1:
    buf.c_write(&val, 1)
    return 0


cdef inline int write_i16(CyTransportBase buf, int16_t val) except -1:
    # 以big endian的方式写数据
    val = htobe16(val)
    buf.c_write(<char*>(&val), 2)
    return 0


cdef inline int write_i32(CyTransportBase buf, int32_t val) except -1:
    val = htobe32(val)
    buf.c_write(<char*>(&val), 4)
    return 0


cdef inline int write_i64(CyTransportBase buf, int64_t val) except -1:
    val = htobe64(val)
    buf.c_write(<char*>(&val), 8)
    return 0


cdef inline int write_double(CyTransportBase buf, double val) except -1:
    cdef int64_t v = htobe64((<int64_t*>(&val))[0])
    buf.c_write(<char*>(&v), 8)
    return 0



# (7, TType.LIST, 'similar_checkups', (TType.STRUCT,(TermCounter, TermCounter.thrift_spec)), None, )
cdef inline write_list(CyTransportBase buf, object val, spec):
    cdef TType e_type
    cdef int val_len

    e_type = spec[0]
    e_spec = spec[1]

    val_len = len(val)
    write_i08(buf, e_type)
    write_i32(buf, val_len)

    for e_val in val:
        c_write_val(buf, e_type, e_val, e_spec)


cdef inline write_string(CyTransportBase buf, bytes val):
    cdef int val_len = len(val)
    write_i32(buf, val_len)

    buf.c_write(<char*>val, val_len)


cdef inline write_dict(CyTransportBase buf, object val, spec):
    cdef int val_len
    cdef TType v_type, k_type

    k_type = spec[0]
    k_spec = spec[1]
    v_type = spec[2]
    v_spec = spec[3]

    val_len = len(val)

    write_i08(buf, k_type)
    write_i08(buf, v_type)
    write_i32(buf, val_len)

    for k, v in val.items():
        c_write_val(buf, k_type, k, k_spec)
        c_write_val(buf, v_type, v, v_spec)


cdef inline read_struct(CyTransportBase buf, obj):
    # obj 为thrift中定义的一个 struct
    # read_struct 按照 obj.thrift_spec的定义，解析其中的字段
    cdef tuple field_specs = obj.thrift_spec
    cdef int fid
    cdef TType field_type, ttype
    cdef tuple field_spec
    cdef str name

    # field_specs 格式:
    #   field_type
    #   fid ---> field_spec

    while True:
        field_type = <TType>read_i08(buf)
        if field_type == T_STOP:
            break

        fid = read_i16(buf)
        if fid >= len(field_specs) or fid < 0 or field_specs[fid] is None:
            skip(buf, field_type)
            continue

        field_spec = field_specs[fid]
        ttype = field_spec[1]
        if field_type != ttype:
            skip(buf, field_type)
            continue

        name = field_spec[2]
        spec = field_spec[3]

        # 将读取的结果 和 name关联
        # (1, TType.STRING, 'city', None, None, )
        # (3, TType.LIST, 'names', (TType.STRING,None), None, )
        # (1, TType.LIST, 'locations', (TType.STRUCT,(Location, Location.thrift_spec)), None, ), # 1
        setattr(obj, name, c_read_val(buf, ttype, spec))

    return obj


cdef inline write_struct(CyTransportBase buf, obj):
    cdef int fid
    cdef TType f_type
    cdef tuple thrift_spec = obj.thrift_spec # 和thrift保持一致
    cdef tuple field_spec
    cdef str f_name

    # writeStructBegin 空操作
    for field_spec in thrift_spec:
        # thrift_spec[0] 为 None，可能为占位符号
        if field_spec is None:
            continue

        # fid = field_spec[0]
        # f_type = field_spec[1]
        f_name = field_spec[2]
        # container_spec = field_spec[3]

        v = getattr(obj, f_name)
        if v is None:
            continue


        fid = field_spec[0]
        f_type = field_spec[1]
        container_spec = field_spec[3]
        # print "fid: %s, f_type: %s" % (fid, f_type)
        # (3, TType.LIST, 'names', (TType.STRING,None), None, )
        # (1, TType.LIST, 'locations', (TType.STRUCT,(Location, Location.thrift_spec)), None, ), # 1

        # writeFieldBegin
        write_i08(buf, f_type)  # writeByte
        write_i16(buf, fid)     # writeI16
        try:
            c_write_val(buf, f_type, v, container_spec)
        except (TypeError, AttributeError, AssertionError, OverflowError):
            raise TDecodeException(obj.__class__.__name__, fid, f_name, v,
                                   f_type, container_spec)

    write_i08(buf, T_STOP) # writeFieldStop


cdef inline c_read_string(CyTransportBase buf, int32_t size):
    cdef char string_val[STACK_STRING_LEN]

    if size > STACK_STRING_LEN:
        data = <char*>malloc(size)
        buf.c_read(size, data)
        py_data = data[:size]
        free(data)
    else:
        buf.c_read(size, string_val)
        py_data = string_val[:size]

    try:
        return py_data.decode("utf-8")
    except UnicodeDecodeError:
        return py_data


cdef c_read_val(CyTransportBase buf, TType ttype, spec=None):
    cdef int size
    cdef int64_t n
    cdef TType v_type, k_type, orig_type, orig_key_type

    if ttype == T_BOOL:
        return bool(read_i08(buf))

    elif ttype == T_I08:
        return read_i08(buf)

    elif ttype == T_I16:
        return read_i16(buf)

    elif ttype == T_I32:
        return read_i32(buf)

    elif ttype == T_I64:
        return read_i64(buf)

    elif ttype == T_DOUBLE:
        n = read_i64(buf)
        return (<double*>(&n))[0]

    elif ttype == T_STRING:
        size = read_i32(buf)
        return c_read_string(buf, size)

    elif ttype == T_SET or ttype == T_LIST:
        # (3, TType.LIST, 'names', (TType.STRING,None), None, )
        # (1, TType.LIST, 'locations', (TType.STRUCT,(Location, Location.thrift_spec)), None, ), # 1
        # (7, TType.LIST, 'loc_list', (TType.STRUCT,(Location, Location.thrift_spec)), None, ), # 7
        # (8, TType.LIST, 'list_map', (TType.MAP,(TType.I32,None,TType.STRUCT,(Location, Location.thrift_spec))), None, ), # 8
        #
        # list/set之后的元素要么是简单类型: int, string等
        #                  要么是复杂类型，
        v_type = spec[0]
        v_spec = spec[1]

        orig_type = <TType>read_i08(buf)
        size = read_i32(buf)

        if orig_type != v_type:
            for _ in range(size):
                skip(buf, orig_type)
            return []

        return [c_read_val(buf, v_type, v_spec) for _ in range(size)]

    elif ttype == T_MAP:
        # (4, TType.MAP, 'id2name', (TType.I32,None,TType.STRING,None), None, ), # 4
        # (5, TType.MAP, 'id2loc', (TType.I32,None,TType.STRUCT,(Location, Location.thrift_spec)), None, ), # 5

        k_type = spec[0]
        k_spec = spec[1]

        v_type = spec[2]
        v_spec = spec[3]

        # 读取key_type, value_type, size
        orig_key_type = <TType>read_i08(buf)
        orig_type = <TType>read_i08(buf)
        size = read_i32(buf)

        # 认为数据是一致的
        if orig_key_type != k_type or orig_type != v_type:
            for _ in range(size):
                skip(buf, orig_key_type)
                skip(buf, orig_type)
            return {}

        return {c_read_val(buf, k_type, k_spec): c_read_val(buf, v_type, v_spec) for _ in range(size)}

    elif ttype == T_STRUCT:
        # (6, TType.STRUCT, 'loc', (Location, Location.thrift_spec), None, ), # 6
        # spec格式: (Location, Location.thrift_spec)
        #   spec[0] 表示 struct的类型, spec[1] 没有必要直接使用
        #   spec[0]() 构造struct对象
        return read_struct(buf, spec[0]())


cdef c_write_val(CyTransportBase buf, TType ttype, val, spec=None):
    if ttype == T_BOOL:
        write_i08(buf, 1 if val else 0)

    elif ttype == T_I08:
        write_i08(buf, val)

    elif ttype == T_I16:
        write_i16(buf, val)

    elif ttype == T_I32:
        write_i32(buf, val)

    elif ttype == T_I64:
        write_i64(buf, val)

    elif ttype == T_DOUBLE:
        write_double(buf, val)

    elif ttype == T_STRING:
        #  确保为utf8格式的bytes
        if not isinstance(val, bytes):
            try:
                val = val.encode("utf-8")
            except Exception:
                pass
        write_string(buf, val)

    elif ttype == T_SET or ttype == T_LIST:
        assert not isinstance(val, basestring)
        write_list(buf, val, spec)

    elif ttype == T_MAP:
        write_dict(buf, val, spec)

    elif ttype == T_STRUCT:
        write_struct(buf, val)


cpdef skip(CyTransportBase buf, TType ttype):
    cdef TType v_type, k_type, f_type
    cdef int size

    if ttype == T_BOOL or ttype == T_I08:
        read_i08(buf)
    elif ttype == T_I16:
        read_i16(buf)
    elif ttype == T_I32:
        read_i32(buf)
    elif ttype == T_I64 or ttype == T_DOUBLE:
        read_i64(buf)
    elif ttype == T_STRING:
        size = read_i32(buf)
        c_read_string(buf, size)
    elif ttype == T_SET or ttype == T_LIST:
        v_type = <TType>read_i08(buf)
        size = read_i32(buf)
        for _ in range(size):
            skip(buf, v_type)
    elif ttype == T_MAP:
        k_type = <TType>read_i08(buf)
        v_type = <TType>read_i08(buf)
        size = read_i32(buf)
        for _ in range(size):
            skip(buf, k_type)
            skip(buf, v_type)
    elif ttype == T_STRUCT:
        while 1:
            f_type = <TType>read_i08(buf)
            if f_type == T_STOP:
                break
            read_i16(buf)
            skip(buf, f_type)


def read_val(CyTransportBase buf, TType ttype):
    return c_read_val(buf, ttype)


def write_val(CyTransportBase buf, TType ttype, val, spec=None):
    c_write_val(buf, ttype, val, spec)


cdef class TCyBinaryProtocol(object):
    cdef:
        public CyTransportBase trans
        bool strict_read
        bool strict_write
        str  service
        object logger
        double lastWriteTime


    def __init__(self, trans, strict_read=True, strict_write=True, service=None, logger=None):
        self.trans = trans
        self.strict_read = strict_read
        self.strict_write = strict_write
        self.service = service
        self.logger = logger

    def skip(self, ttype):
        skip(self.trans, <TType>(ttype))

    cpdef readMessageBegin(self):
        cdef int32_t size, version, seqid
        cdef TType ttype
        cdef double elapsed;

        size = read_i32(self.trans)
        if size < 0:
            version = size & VERSION_MASK
            if version != VERSION_1:
                raise ProtocolError('invalid version %d' % version)

            name = c_read_val(self.trans, T_STRING)
            ttype = <TType>(size & TYPE_MASK)
        else:
            if self.strict_read:
                raise ProtocolError('No protocol version header')

            name = c_read_string(self.trans, size)
            ttype = <TType>(read_i08(self.trans))

        seqid = read_i32(self.trans)

        elapsed = (time() - self.lastWriteTime) * 1000
        if self.logger:
            method = self.service + ":" + name
            self.logger.info("\033[35m[RPC] %s\033[39m[%d] ends, Elapsed: %.3fms", method, seqid, elapsed)


        return name, ttype, seqid

    def readMessageEnd(self):
        pass

    cpdef writeMessageBegin(self, name, TType ttype, int32_t seqid):
        cdef int32_t version = VERSION_1 | ttype

        self.lastWriteTime = time()

        if self.strict_write:
            write_i32(self.trans, version)
            if self.service:
                c_write_val(self.trans, T_STRING, self.service + ":" + name)
            else:
                c_write_val(self.trans, T_STRING, name)
        else:
            if self.service:
                c_write_val(self.trans, T_STRING, self.service + ":" + name)
            else:
                c_write_val(self.trans, T_STRING, name)

            write_i08(self.trans, ttype)

        write_i32(self.trans, seqid)

    def writeMessageEnd(self):
        self.trans.c_flush()

    def read_struct(self, obj):
        try:
            return read_struct(self.trans, obj)
        except Exception:
            self.trans.clean()
            raise

    def write_struct(self, obj):
        try:
            write_struct(self.trans, obj)
        except Exception:
            self.trans.clean()
            raise


class TCyBinaryProtocolFactory(object):
    def __init__(self, strict_read=True, strict_write=True):
        self.strict_read = strict_read
        self.strict_write = strict_write

    def get_protocol(self, trans):
        return TCyBinaryProtocol(trans, self.strict_read, self.strict_write)
