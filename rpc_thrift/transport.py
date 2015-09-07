# -*- coding: utf-8 -*-
from __future__ import absolute_import

import socket
from struct import pack, unpack
import errno
import sys
from StringIO import StringIO
from thrift.transport.TSocket import TSocketBase

from thrift.transport.TTransport import TTransportBase, TTransportException


class TSocket(TSocketBase):
    """Socket implementation of TTransport base."""

    def __init__(self, host='localhost', port=9090, unix_socket=None, socket_family=socket.AF_UNSPEC):
        """Initialize a TSocket

        @param host(str)  The host to connect to.
        @param port(int)  The (TCP) port to connect to.
        @param unix_socket(str)  The filename of a unix socket to connect to.
                                 (host and port will be ignored.)
        @param socket_family(int)  The socket family to use with this socket.
        """
        self.host = host
        self.port = port
        self.handle = None
        self._unix_socket = unix_socket
        self._timeout = None
        self._socket_family = socket_family

    def setHandle(self, h):
        self.handle = h

    def isOpen(self):
        return self.handle is not None

    def setTimeout(self, ms):
        if ms is None:
            self._timeout = None
        else:
            self._timeout = ms / 1000.0

        if self.handle is not None:
            self.handle.settimeout(self._timeout)

    def open(self):
        try:
            res0 = self._resolveAddr()
            for res in res0:
                self.handle = socket.socket(res[0], res[1])
                self.handle.settimeout(self._timeout)
                # 拷贝自redis-py
                if res[0] == socket.AF_INET:
                    self.handle.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                try:
                    self.handle.connect(res[4])
                except socket.error, e:
                    if res is not res0[-1]:
                        continue
                    else:
                        raise e
                break
        except socket.error, e:
            # 遇到这种socket的Error, 似乎没有必要Retry, 直接报错
            if self._unix_socket:
                message = 'Could not connect to socket %s' % self._unix_socket
            else:
                message = 'Could not connect to %s:%d' % (self.host, self.port)
            raise TTransportException(type=TTransportException.NOT_OPEN, message=message)

    def read(self, sz):
        try:
            # 正常情况下会block在这个地方，直到读取所需要sz的数据
            buff = self.handle.recv(sz)
        except socket.error, e:
            if (e.args[0] == errno.ECONNRESET and
                    (sys.platform == 'darwin' or sys.platform.startswith('freebsd'))):
                # freebsd and Mach don't follow POSIX semantic of recv
                # and fail with ECONNRESET if peer performed shutdown.
                # See corresponding comment and code in TSocket::read()
                # in lib/cpp/src/transport/TSocket.cpp.
                self.close()
                # Trigger the check to raise the END_OF_FILE exception below.
                buff = ''
            else:
                raise
        if len(buff) == 0:
            raise TTransportException(type=TTransportException.END_OF_FILE,
                                      message='TSocket read 0 bytes')
        return buff

    def write(self, buff):
        if not self.handle:
            raise TTransportException(type=TTransportException.NOT_OPEN,
                                      message='Transport not open')
        sent = 0
        have = len(buff)
        while sent < have:
            plus = self.handle.send(buff)
            if plus == 0:
                raise TTransportException(type=TTransportException.END_OF_FILE,
                                          message='TSocket sent 0 bytes')
            sent += plus
            buff = buff[plus:]

    def flush(self):
        pass


class TFramedTransportEx(TTransportBase):
    """
        和 TFramedTransport的区别:
            多了一个 readFrameEx 函数, 由于 TFramedTransport 中的变量 __wbuf, __rbuf不能直接访问，因此就重写了该类
    """

    def __init__(self, trans, ):
        self.trans = trans
        self.wbuf = StringIO()
        self.rbuf = StringIO()

    def readFrameEx(self):
        """
            直接以bytes的形式返回一个Frame
        """
        buff = self.trans.readAll(4)
        sz, = unpack('!i', buff)

        bytes = self.trans.readAll(sz)
        return bytes


    def isOpen(self):
        return self.trans.isOpen()

    def open(self):
        return self.trans.open()

    def close(self):
        return self.trans.close()


    def read(self, sz):
        ret = self.rbuf.read(sz)
        if len(ret) != 0:
            return ret

        self.readFrame()
        return self.rbuf.read(sz)


    def readFrame(self):
        buff = self.trans.readAll(4)
        sz, = unpack('!i', buff)
        self.rbuf = StringIO(self.trans.readAll(sz))


    def write(self, buf):
        self.wbuf.write(buf)

    def flush(self):
        wout = self.wbuf.getvalue()
        wsz = len(wout)
        self.wbuf = StringIO()

        # print "TFramedTransport#Flush Frame Size: ", wsz

        # 首先写入长度，并且Flush之前的数据
        self.trans.write(pack("!i", wsz) + wout)
        # self.trans.write(wout)
        self.trans.flush()


class TAutoConnectFramedTransport(TTransportBase):
    """
        将socket进行包装，提供了自动重连的功能, 重连之后清空之前的状态
    """

    def __init__(self, socket):
        self.socket = socket

        self.wbuf = StringIO()
        self.rbuf = StringIO()

    def isOpen(self):
        return self.socket.isOpen()

    def open(self):
        """
            open之后需要重置状态
        """
        self.socket.open()

        # 恢复状态
        self.reset_buff()

    def close(self):
        self.socket.close()

    def reset_buff(self):
        if self.wbuf.len != 0:
            self.wbuf = StringIO()
        if self.rbuf.len != 0:
            self.rbuf = StringIO()

    def read(self, sz):
        if not self.isOpen():
            self.open()

        ret = self.rbuf.read(sz)
        if len(ret) != 0:
            return ret

        try:
            self.__readFrame()
            return self.rbuf.read(sz)
        except Exception:  # TTransportException, timeout, Broken Pipe
            self.close()
            raise

    def __readFrame(self):
        buff = self.socket.readAll(4)
        sz, = unpack('!i', buff)
        self.rbuf = StringIO(self.socket.readAll(sz))


    def write(self, buf):
        if not self.isOpen():
            self.open()
        self.wbuf.write(buf)

    def flush(self):
        if not self.isOpen():
            self.open()

        wout = self.wbuf.getvalue()
        wsz = len(wout)
        self.wbuf = StringIO()  # 状态恢复了

        # print "TFramedTransport#Flush Frame Size: ", wsz
        try:
            # 首先写入长度，并且Flush之前的数据
            self.socket.write(pack("!i", wsz) + wout)
            self.socket.flush()
        except Exception:
            self.close()
            raise


class TMemoryBuffer(TTransportBase):
    def __init__(self, value=None):
        if value is not None:
            if isinstance(value, StringIO):
                self._buffer = value
            else:
                self._buffer = StringIO(value)
        else:
            self._buffer = StringIO()

    def isOpen(self):
        return not self._buffer.closed

    def open(self):
        pass

    def close(self):
        self._buffer.close()

    def read(self, sz):
        return self._buffer.read(sz)

    def write(self, buf):
        self._buffer.write(buf)

    def flush(self):
        pass

    def getvalue(self):
        return self._buffer.getvalue()
