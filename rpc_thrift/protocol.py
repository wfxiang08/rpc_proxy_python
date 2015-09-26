# -*- coding: utf-8 -*-
from __future__ import absolute_import
import time

from thrift.protocol import TBinaryProtocol as TBinaryProtocolPack
from thrift.protocol.TBinaryProtocol import TBinaryProtocol
from thrift.Thrift import TMessageType



# TBinaryProtocolAccelerated 自动支持utf8
# 不要使用: TProtocolDecorator, hasattr, getattr等非常慢

SEPARATOR = ":"

class TUtf8BinaryProtocol(TBinaryProtocol):

    def __init__(self, trans, service_name=None, fastbinary=False, logger=None):
        TBinaryProtocol.__init__(self, trans, False, True)
        if service_name:
            self.service_name_ = service_name + SEPARATOR
        else:
            self.service_name_ = None
        self.fastbinary = fastbinary
        self.logger = logger
        self.last_name = None
        self.start = None





        if self.fastbinary:
            TBinaryProtocolPack.TBinaryProtocolAccelerated = TUtf8BinaryProtocol

    def writeString(self, v):
        """
            只要控制好了writeString, 在整个thrift系统中，所有的字符串都是utf-8格式的
        """
        if isinstance(v, unicode):
            v = v.encode("utf-8")

        # TBinaryProtocol 为 old style class
        TBinaryProtocol.writeString(self, v)


    def writeMessageBegin(self, name, type, seqid):

        self.start = time.time()
        if (type == TMessageType.CALL or type == TMessageType.ONEWAY) and self.service_name_:
            self.last_name = self.service_name_ + name
            TBinaryProtocol.writeMessageBegin(self, self.last_name, type, seqid)
        else:
            self.last_name = name
            TBinaryProtocol.writeMessageBegin(self, name, type, seqid)


    def readMessageBegin(self):
        self.trans.read(4)  # 跳过4字节的FrameSize

        name, type, seqid = TBinaryProtocol.readMessageBegin(self)

        if self.logger:
            # 开始读到了，才打印
            elapsed = (time.time() - self.start) * 1000
            self.logger.info("\033[35m[RPC] %s\033[39m[%s] ends, Elapsed: %.3fms", self.last_name, seqid, elapsed)
        return name, type, seqid



