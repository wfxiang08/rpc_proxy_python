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


class TRBuffSocket(TSocketBase):
    __slots__ = ("host", "port", "_unix_socket", "_socket_family", "_timeout", "socket", "socket_buf", "handle")

    """
        1. 支持 inet, unix domain socket通信的socket
        2. 带有read buffer的socket, 算法来自redis-py
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


PLACE_HOLDER_4_bytes = "1234"

class TAutoConnectFramedTransport(TTransportBase):
    """
        将socket进行包装，提供了自动重连的功能, 重连之后清空之前的状态
    """

    def __init__(self, socket):
        assert isinstance(socket, TRBuffSocket)
        self.socket = socket
        self.socket_buf = self.socket.socket_buf

        self.wbuf = StringIO()
        self.reset_wbuf()


    def isOpen(self):
        return self.socket.isOpen()

    def open(self):
        """
            open之后需要重置状态
        """
        self.socket.open()


    def reset_wbuf(self):
        # 恢复状态
        self.wbuf.reset()
        self.wbuf.write(PLACE_HOLDER_4_bytes)

    def close(self):
        self.socket.close()
        self.reset_wbuf()

    def read(self, sz):
        # Frame相关的信息在Protocol中处理掉了
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


    def write(self, buf):
        self.wbuf.write(buf)

    def flush(self):
        # 1. 在flush时才确保连接打开
        if not self.isOpen():
            self.open()

        wout = get_framed_value(self.wbuf)

        try:
            # 首先写入长度，并且Flush之前的数据
            self.socket.write(wout)
            self.socket.flush()
        except Exception:
            self.close()
            raise

def get_framed_value(wbuf):
    """
        从cStringIO.StringO中读取出带有长度的一帧数据
    """
    # 将wbuf的头四个字节修改为frame的长度
    wsz = wbuf.tell()
    wbuf.seek(0, 0)
    size = wsz - 4
    wbuf.write(pack("!i", size))
    wbuf.seek(wsz, 0)

    wout = wbuf.getvalue(True)

    wbuf.seek(4, 0) # 再次预留4个字节的空间
    return wout



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

    def reset(self):
        self._buffer.reset()
    def write(self, buf):
        # print "Buff: ", ["%03d" % ord(i) for i in buf]
        self._buffer.write(buf)

    def get_raw_value(self):
        return self._buffer.getvalue(True)

    def getvalue(self):
        """
        只给可写的StringIO提供支持, 返回的是 string, 也就是只读的
        """
        return get_framed_value(self._buffer)


    def isOpen(self):
        return not self._buffer.closed

    def open(self):
        pass

    def close(self):
        self._buffer.close()

    def flush(self):
        pass


