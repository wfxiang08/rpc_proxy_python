from thrift.Thrift import TException

__author__ = 'feiwang'
class TDecodeException(TException):
    def __init__(self, name, fid, field, value, ttype, spec=None):
        self.struct_name = name
        self.fid = fid
        self.field = field
        self.value = value

        self.type_repr = "" # parse_spec(ttype, spec)

    def __str__(self):
        return (
            "Field '%s(%s)' of '%s' needs type '%s', "
            "but the value is `%r`"
        ) % (self.field, self.fid, self.struct_name, self.type_repr,
             self.value)