# -*- coding: utf-8 -*-
from __future__ import absolute_import

import socket
from struct import pack, unpack
import errno
import sys
from cStringIO import StringIO
from thrift.transport.TSocket import TSocketBase

from thrift.transport.TTransport import TTransportBase, TTransportException, CReadableTransport
from rpc_thrift.socket_buffer import SocketBuffer


class TSocket(TSocketBase):
    """
        1. 支持 inet, unix domain socket通信的socket
        2. 带有read buffer的socket, 算法来自redis-py
        3.
    """
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

        self._unix_socket = unix_socket
        self._socket_family = socket_family

        self._timeout = None

        self.socket = None
        self.socket_buf = SocketBuffer()
        self.handle = None

    def setHandle(self, h):
        self.setSocket(h)

    def setSocket(self, s):
        """
            更新Socket, 以及对应的SocketBuffer
        """
        self.socket = s
        self.socket_buf.update_socket(self.socket)

    def isOpen(self):
        return self.socket is not None

    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None
            self.socket_buf.update_socket(self.socket)


    def setTimeout(self, ms):
        if ms is None:
            self._timeout = None
        else:
            self._timeout = ms / 1000.0

        if self.socket is not None:
            self.socket.settimeout(self._timeout)

    def open(self):
        try:
            res0 = self._resolveAddr()
            for res in res0:
                self.socket = socket.socket(res[0], res[1])
                self.socket.settimeout(self._timeout)
                self.socket_buf.update_socket(self.socket)

                # 拷贝自redis-py
                if res[0] == socket.AF_INET:
                    self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                try:
                    self.socket.connect(res[4])
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

    def read_complete(self):
        return self.socket_buf.read_complete()

    def peek(self, sz):
        """
        确保socket中存在 sz个字节
        :param sz:
        :return:
        """
        try:
            self.socket_buf.peek(sz)
        except socket.error, e:
            if (e.args[0] == errno.ECONNRESET and (sys.platform == 'darwin' or sys.platform.startswith('freebsd'))):
                # freebsd and Mach don't follow POSIX semantic of recv and fail with ECONNRESET if peer performed shutdown.
                # See corresponding comment and code in TSocket::read() in lib/cpp/src/transport/TSocket.cpp.
                self.close()
                raise TTransportException(type=TTransportException.END_OF_FILE, message='TSocket read 0 bytes')
            else:
                raise

    def read(self, sz):
        try:
            # 正常情况下会block在这个地方，直到读取所需要sz的数据
            buff = self.socket_buf.read(sz)
        except socket.error, e:
            if (e.args[0] == errno.ECONNRESET and (sys.platform == 'darwin' or sys.platform.startswith('freebsd'))):
                # freebsd and Mach don't follow POSIX semantic of recv and fail with ECONNRESET if peer performed shutdown.
                # See corresponding comment and code in TSocket::read() in lib/cpp/src/transport/TSocket.cpp.
                #
                self.close()
                # Trigger the check to raise the END_OF_FILE exception below.
                buff = ''
            else:
                raise

        if len(buff) == 0:
            raise TTransportException(type=TTransportException.END_OF_FILE,
                                      message='TSocket read 0 bytes')
        else:
            return buff

    def readAll(self, sz):
        """
        由于存在buffer, 因此应该能够一口气读取完毕
        :param sz:
        :return:
        """
        return self.read(sz)

    def unread(self, sz):
        self.socket_buf.unread(sz)

    def write(self, buff):
        if not self.socket:
            raise TTransportException(type=TTransportException.NOT_OPEN,
                                      message='Transport not open')
        try:
            self.socket.sendall(buff)
        except socket.timeout:
            raise TTransportException(type=TTransportException.TIMED_OUT,
                                      message='Socket Timeout')
        except socket.error:
            raise TTransportException(type=TTransportException.UNKNOWN,
                                      message='Socket Send Error')

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

READ_BUFFER = 1024 * 4
PLACE_HOLDER_4_bytes = "1234"
class TAutoConnectFramedTransport(TTransportBase): # CReadableTransport
    """
        将socket进行包装，提供了自动重连的功能, 重连之后清空之前的状态
    """

    def __init__(self, socket):
        self.socket = socket        # TSocket

        # StringIO的两种状态:
        #   cStringIO.InputType
        #   cStringIO.OutputType
        self.wbuf = StringIO()


    def isOpen(self):
        return self.socket.isOpen()

    def open(self):
        """
            open之后需要重置状态
        """
        self.socket.open()
        self.reset_wbuf()

    def reset_wbuf(self):
        # 恢复状态
        self.wbuf.reset()
        self.wbuf.write(PLACE_HOLDER_4_bytes)

    def close(self):
        self.socket.close()

    def read(self, sz):
        # 1. 先预先读取一帧数据
        if self.socket.read_complete():
            # 2. 读取一帧数据
            try:
                self.__readFrame()
            except Exception:  # TTransportException, timeout, Broken Pipe
                self.close()
                raise

        # 2. 在buffer上读取数据
        if sz > 0:
            try:
                return self.socket.readAll(sz)
            except Exception:
                self.close()
                raise
        else:
            return ""

    def readAll(self, sz):
        # 由于buffer的存在, readAll功能退化
        return self.read(sz)


    def __readFrame(self):
        buff = self.socket.readAll(4)
        sz, = unpack('!i', buff)
        # socket预先读取这么多的字节
        self.socket.peek(sz)


    def write(self, buf):
        # 1. 在flush时才确保连接打开
        if not self.isOpen():
            self.open()

        self.wbuf.write(buf)

    def flush(self):
        # 2. 将wbuf的头四个字节修改为frame的长度
        wsz = self.wbuf.tell()
        self.wbuf.seek(0, 0)
        size = wsz - 4
        self.wbuf.write(pack("!i", size))
        self.wbuf.seek(wsz, 0)

        wout = self.wbuf.getvalue(True)

        try:
            # 首先写入长度，并且Flush之前的数据
            self.socket.write(wout)
            self.socket.flush()

            self.reset_wbuf()
        except Exception:
            self.reset_wbuf()
            self.close()
            raise


    # @property
    # def cstringio_buf(self):
    #     return self.rbuf
    #
    #
    # def cstringio_refill(self, partialread, reqlen):
    #     """
    #         一次读一个Frame
    #     """
    #     self.__readFrame() # 不应该有partialread
    #     # retstring = partialread
    #     # if reqlen < self.__rbuf_size:
    #     #     # try to make a read of as much as we can.
    #     #     retstring += self.__trans.read(self.__rbuf_size)
    #     #
    #     # # but make sure we do read reqlen bytes.
    #     # if len(retstring) < reqlen:
    #     #     retstring += self.__trans.readAll(reqlen - len(retstring))
    #     #
    #     # self.rbuf = StringIO(retstring)
    #     return self.rbuf

FRAME_SIZE_PLACE_HOLDER = "1234"
class TMemoryBuffer(TTransportBase):
    def __init__(self, value=None):
        if value is not None:
            if hasattr(value, "close") and hasattr(value, "read"):  # isinstance(value, StringIO):
                self._buffer = value
            else:
                # 这个是只读的
                self._buffer = StringIO(value)
        else:
            self._buffer = StringIO()

    def read(self, sz):
        return self._buffer.read(sz)

    def prepare_4_frame(self, placeholder = False):
        if placeholder:
            self._buffer.write(FRAME_SIZE_PLACE_HOLDER)
        else:
            self._buffer.seek(4, 0)
    def update_frame_size(self):
        pos = self._buffer.tell()
        size = pos - 4
        self._buffer.seek(0, 0)
        self._buffer.write(pack("!i", size))
        self._buffer.seek(pos, 0)

    def reset(self):
        self._buffer.reset()
    def write(self, buf):
        self._buffer.write(buf)
    def getvalue(self):
        """
        只给可写的StringIO提供支持, 返回的是 string, 也就是只读的
        """
        return self._buffer.getvalue(True)



    def isOpen(self):
        return not self._buffer.closed

    def open(self):
        pass

    def close(self):
        self._buffer.close()

    def flush(self):
        pass


