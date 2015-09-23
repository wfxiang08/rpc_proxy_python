# -*- coding: utf-8 -*-
from __future__ import absolute_import

import socket
from cStringIO import StringIO

SERVER_CLOSED_CONNECTION_ERROR = "Connection closed by server."
class SocketBuffer(object):
    """
        拷贝自redis-py(目标减少系统调用)
    """
    def __init__(self, socket = None, socket_read_size=65536):
        self._sock = socket
        self.socket_read_size = socket_read_size

        self._buffer = StringIO()
        self.bytes_written = 0      # 从socket写入buffer的 byte数
        self.bytes_read = 0         # 从buffer读取的byte数

    def update_socket(self, socket):
        """
        socket连接成功之后和SocketBuffer绑定
        """
        self._sock = socket
        self.purge()

    @property
    def length(self):
        return self.bytes_written - self.bytes_read

    def read_from_socket(self, length=None):
        """
        确保buffer中的数据足够多
        :param length:
        :return:
        """
        socket_read_size = self.socket_read_size
        buf = self._buffer
        buf.seek(self.bytes_written)
        marker = 0

        try:
            while True:
                data = self._sock.recv(socket_read_size)
                # an empty string indicates the server shutdown the socket
                if isinstance(data, bytes) and len(data) == 0:
                    raise socket.error(SERVER_CLOSED_CONNECTION_ERROR)

                buf.write(data)
                data_length = len(data)
                self.bytes_written += data_length
                marker += data_length

                if length is not None and length > marker:
                    continue
                break
        except socket.timeout:
            raise
        except socket.error:
            raise
            # e = sys.exc_info()[1]
            # raise Exception("Error while reading from socket: %s" % (e.args,))

    def read(self, length):
        # 如果buffer中的数据不够，则从socket读取
        if length > self.length:
            self.read_from_socket(length - self.length)

        # 从_buffer中读取数据
        self._buffer.seek(self.bytes_read)
        data = self._buffer.read(length)

        self.bytes_read += len(data)

        # purge the buffer when we've consumed it all so it doesn't
        # grow forever
        # 什么时候会读取完毕呢?
        # 1. socket也不会无缘无故读取太多的数据，一个Request处理完毕之后，应该就需要purge了
        if self.bytes_read == self.bytes_written:
            self.purge()

        return data

    def read_complete(self):
        """
        当前的数据是否读取完毕
        :return:
        """
        return self.bytes_read == self.bytes_written


    def purge(self):
        self._buffer.seek(0)
        self._buffer.truncate()
        self.bytes_written = 0
        self.bytes_read = 0

    def close(self):
        self.purge()
        self._buffer.close()
        self._buffer = None
        self._sock = None