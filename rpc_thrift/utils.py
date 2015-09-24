# -*- coding: utf-8 -*-
from __future__ import absolute_import

from rpc_thrift.protocol import TUtf8BinaryProtocol
from rpc_thrift.transport import TAutoConnectFramedTransport, TRBuffSocket




# Client目前只考虑单线程的情况, 如果是多线程，或者coroutine可能需要使用pool
_transport = None

def get_base_protocol(endpoint, timeout=5000):
    """
    临时兼容旧的代码
    :param endpoint:
    :param timeout:
    :return:
    """
    return get_transport(endpoint, timeout)

def get_transport(endpoint, timeout=5000):
    global _transport
    if not _transport:
        if endpoint.find(":") != -1:
            hostport = endpoint.split(":")
            host = hostport[0]
            port = int(hostport[1])
            unix_socket = None
        else:
            host = None
            port = None
            unix_socket = endpoint

        socket = TRBuffSocket(host=host, port=port, unix_socket=unix_socket)
        socket.setTimeout(timeout)
        _transport = TAutoConnectFramedTransport(socket)
    return _transport


def get_transport_4_pool(endpoint, timeout=5000):
    if endpoint.find(":") != -1:
        hostport = endpoint.split(":")
        host = hostport[0]
        port = int(hostport[1])
        unix_socket = None
    else:
        host = None
        port = None
        unix_socket = endpoint
    socket = TRBuffSocket(host=host, port=port, unix_socket=unix_socket)
    socket.setTimeout(timeout)
    transport = TAutoConnectFramedTransport(socket)

    return transport


def get_service_protocol(service, transport=None, logger=None, fastbinary=False):
    """
    多个不同的service可以共用一个base_protocol; 如果指定了service, 则在base_protocol的基础上添加一个新的wrap

    TSocket --> TAutoConnectSocket --> TFramedTransport --> TUtf8BinaryProtocol --> TMultiplexedProtocol
                    |
                    |-----------------------------------> 直接合并成为: TAutoConnectFramedTransport, 之后的protocol最好不要带有状态

    存在问题: TFramedTransport存在buf, 自动重连之后状态还存在

    :param service:
    :param base_protocol:
    :return:
    """
    transport = transport or _transport
    return TUtf8BinaryProtocol(transport, service, fastbinary, logger)
