# -*- coding: utf-8 -*-
from __future__ import absolute_import

import time

from rpc_thrift.server import RpcServer, gevent
from rpc_thrift.services.RpcServiceBase import Iface, Processor, Client
from rpc_thrift.utils import get_base_protocol
from rpc_thrift.utils import get_service_protocol


class TypoProcessor(Iface):
    def ping(self):
        # print "Receive Ping Msg"
        pass

TEST_SOCKET="test_0001.sock"

FAST_BINARY=True
def main():
    # 首先启动这样的一个Server
    endpoint = TEST_SOCKET
    service = "test"
    worker_pool_size = 1

    processor = Processor(TypoProcessor())
    # 如何判断当前的Queue是否已经挂了
    s = RpcServer(processor, endpoint, pool_size=worker_pool_size,service=service)

    r1 = gevent.spawn(s.run)


    r2 = gevent.spawn(client_test, s)

    gevent.joinall([r1, r2]) # 测试完毕即可退出

def client_test(server):
    gevent.sleep(1)
    service = ""
    endpoint = TEST_SOCKET
    get_base_protocol(endpoint, timeout=5000)
    protocol = get_service_protocol(service, fastbinary=FAST_BINARY)
    client = Client(protocol)

    print "Begin Request"
    try:
        t = time.time()
        total_times = 10000
        for i in xrange(total_times):
            client.ping()
        t = time.time() - t
        print "AVG RT: %.3fms" % (t * 1000 / total_times)
    finally:
        server.stop()


if __name__ == "__main__":

    main()






