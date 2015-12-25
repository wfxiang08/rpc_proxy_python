from thrift.Thrift import TException

__author__ = 'feiwang'

class TDecodeException(TException):
    def __init__(self, name, fid, field, value, message=""):
        TException.__init__(self, message)

        self.struct_name = name
        self.fid = fid
        self.field = field
        self.value = value


    def __str__(self):
        return ("Field '%s(%s)' of '%s' Exception: %s") % (self.field, self.fid, self.struct_name, self.message)