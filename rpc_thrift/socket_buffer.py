# -*- coding: utf-8 -*-
from __future__ import absolute_import

import socket

from cStringIO import StringIO

import sys

is_new_buffer = sys.version_info > (2, 7, 5)

SERVER_CLOSED_CONNECTION_ERROR = "Connection closed by server."
class SocketBuffer(object):
    __slots__ = ("_sock", "socket_read_size", "_buffer", "bytes_written")
    # , "byte_array", "byte_array0"
    """
        拷贝自redis-py(目标减少系统调用)
    """
    def __init__(self, socket = None, socket_read_size=1024 * 64):
        self._sock = socket
        self.socket_read_size = socket_read_size

        self._buffer = StringIO()
        self.bytes_written = 0      # 从socket写入buffer的 byte数


    def update_socket(self, socket):
        """
        socket连接成功之后和SocketBuffer绑定
        """
        self._sock = socket
        self.purge()

    def _read_from_socket(self, length=None):
        """
            从socket中新读取一个数据包(recv能读取多少就读取多少)，或者读取指定长度的数据
            注意两个状态变量:
                self.bytes_written
                self.bytes_read
        """


        socket_read_size = self.socket_read_size
        buf = self._buffer
        bytes_read = buf.tell()
        buf.seek(self.bytes_written)
        marker = 0

        try:
            while True:
                data = self._sock.recv(socket_read_size)
                # data_length = self._sock.recv_into(self.byte_array, socket_read_size)
                # an empty string indicates the server shutdown the socket
                if isinstance(data, bytes) and len(data) == 0:
                # if data_length == 0:
                    raise socket.error(SERVER_CLOSED_CONNECTION_ERROR)

                # if is_new_buffer:
                #     buf.write(self.byte_array[0:data_length])
                # else:
                #     buf.write(buffer(self.byte_array0, 0, data_length))
                buf.write(data)
                data_length = len(data)
                self.bytes_written += data_length
                marker += data_length

                if (length is not None) and length > marker:
                    continue

                # 还原buf的pos
                buf.truncate(self.bytes_written)
                buf.seek(bytes_read)
                break

        except socket.timeout:
            raise
        except socket.error:
            raise
            # e = sys.exc_info()[1]
            # raise Exception("Error while reading from socket: %s" % (e.args,))

    def unread(self, size):
        pos = self._buffer.tell()
        if  pos >= size:
            self._buffer.seek(pos - size, 0)
        else:
            raise socket.error("Unexpceted bytes_read status")

    def peek(self, length):
        # 如果buffer中的数据不够，则从socket读取
        pos = self._buffer.tell()
        if pos + length > self.bytes_written:
            self._read_from_socket(pos + length - self.bytes_written)


    def read(self, length):
        # 如果buffer中的数据不够，则从socket读取
        pos = self._buffer.tell()
        if pos + length > self.bytes_written:
            self._read_from_socket(pos + length - self.bytes_written)

        # 从_buffer中读取数据

        data = self._buffer.read(length)


        # purge the buffer when we've consumed it all so it doesn't
        # grow forever
        # 什么时候会读取完毕呢?
        # 1. socket也不会无缘无故读取太多的数据，一个Request处理完毕之后，应该就需要purge了
        if self._buffer.tell() == self.bytes_written:
            self.purge()

        return data


    def purge(self):
        self._buffer.seek(0)
        self._buffer.truncate()
        self.bytes_written = 0

    def close(self):
        self.purge()
        self._buffer.close()
        self._buffer = None
        self._sock = None