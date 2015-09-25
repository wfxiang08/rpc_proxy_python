# -*- coding: utf-8 -*-
from __future__ import absolute_import

import collections
import logging
import os
import signal
import time
import traceback
from struct import unpack

from colorama import Fore
import gevent.pool
import gevent.queue
import gevent.event
import gevent.local
import gevent.lock
from thrift.Thrift import TApplicationException, TMessageType
from thrift.transport.TSocket import TServerSocket
from thrift.transport.TTransport import TTransportException

from rpc_thrift import MESSAGE_TYPE_HEART_BEAT
from rpc_thrift.config import print_exception
from rpc_thrift.heartbeat import new_rpc_exit_message
from rpc_thrift.protocol import TUtf8BinaryProtocol
from rpc_thrift.transport import TMemoryBuffer, TRBuffSocket


info_logger = logging.getLogger('info_logger')

class TServerSocketEx(TServerSocket):
  def accept(self):
        client, addr = self.handle.accept()
        result = TRBuffSocket()
        result.setHandle(client)
        return result

class RpcServer(object):
    def __init__(self, processor, address, pool_size=5, service=None, fastbinary=False):
        self.processor = processor

        if address.find(":") != -1:
            address = address.split(":")
            self.host = address[0]
            self.port = int(address[1])
            self.unix_socket = None
        else:
            self.host = None
            self.port = None
            self.unix_socket = address

        self.fastbinary = fastbinary
        # 4. gevent
        self.task_pool = gevent.pool.Pool(size=pool_size)
        self.acceptor_task = None

        # 5. 程序退出控制
        self.alive = True
        self.reconnect_interval = 1

        self.responses = []

        self.service = service
        self.queue = None
        self.last_request_time = 0

        self.out_protocols = collections.deque()
        self.alive = True
        self.socket = None

    def close(self):
        self.alive = False
        if self.socket:
            self.socket.close()

    def handle_request(self, proto_input, queue, request_meta):
        """
            从 proto_input中读取数据，然后调用processor处理请求，结果暂时缓存在内存中, 最后一口气交给 queue,
            由专门的 greenlet将数据写回到socket上
            request_meta = (name, type, seqid)
        """

        # 1. 获取一个可用的trans_output
        if len(self.out_protocols) > 0:
            trans_output, proto_output = self.out_protocols.popleft()
            trans_output.prepare_4_frame() # 预留4个字节的Frame Size
        else:
            trans_output = TMemoryBuffer()
            trans_output.prepare_4_frame(True)
            proto_output = TUtf8BinaryProtocol(trans_output) # 无状态的


        try:
            # 2.1 处理正常的请求
            self.processor.process(proto_input, proto_output)
            msg = trans_output.getvalue()
            queue.put(msg)

        except Exception as e:
            # 2.2 处理异常(主要是结果序列化时参数类型不对的情况)

            trans_output.prepare_4_frame()
            name = request_meta[0]
            seqId = request_meta[2]

            msg = '%s, Exception: %s, Trace: %s' % (name, e, traceback.format_exc())
            x = TApplicationException(TApplicationException.INVALID_PROTOCOL, msg)
            proto_output.writeMessageBegin(name, TMessageType.EXCEPTION, seqId)
            x.write(proto_output)
            proto_output.writeMessageEnd()
            proto_output.trans.flush()

            queue.put(trans_output.getvalue())

        finally:
            # 3. 回收 transport 和 protocol
            self.out_protocols.append((trans_output, proto_output))


    def loop_all(self):
        socket = TServerSocketEx(host=self.host, port=self.port, unix_socket=self.unix_socket)
        socket.open()
        socket.listen()

        while self.alive:
            tsocket = socket.accept()
            print "Get A Connection: ", tsocket

            # 如果出现None, 则表示要结束了
            queue = gevent.queue.Queue()

            # 3. 在同一个transport上进行读写数据
            g1 = gevent.spawn(self.loop_reader, tsocket, queue)
            g2 = gevent.spawn(self.loop_writer, tsocket, queue)
            gevent.joinall([g1, g2])


            # 4. 关闭连接
            try:
                print "Trans Closed, queue size: ", queue.qsize()
                tsocket.close()
            except:
                print_exception(info_logger)
                pass


    def loop_reader(self, socket, queue):
        """
        :param tsocket:
        :param queue:
        :return:
        """
        """
        :param tsocket:
        :param queue:
        :return:
        """
        last_hb_time = time.time()

        while True:
            try:
                # 1. 读取一帧数据
                buff = socket.readAll(4)
                sz, = unpack('!i', buff)

                # 将frame size和frame一口气读完, 便于处理"心跳"
                socket.unread(4)
                frame = socket.readAll(4 + sz)

                trans_input = TMemoryBuffer(frame)
                proto_input = TUtf8BinaryProtocol(trans_input, fastbinary=self.fastbinary)
                name, type, seqid = proto_input.readMessageBegin()


                # 如果是心跳，则直接返回
                if type == MESSAGE_TYPE_HEART_BEAT:
                    queue.put(frame)
                    last_hb_time = time.time()
                    # print "Received Heartbeat Signal........"
                    continue

                else:
                    self.last_request_time = time.time()
                    trans_input.reset()
                    self.task_pool.spawn(self.handle_request, proto_input, queue, (name, type, seqid))
            except TTransportException as e:
                # EOF是很正常的现象
                if e.type != TTransportException.END_OF_FILE:
                    print_exception(info_logger)
                info_logger.warning("....Worker Connection To LB Failed, LoopWrite Stop")
                queue.put(None)  # 表示要结束了
                break
            except:
                print_exception(info_logger)
                queue.put(None)  # 表示要结束了
                break


    def loop_writer(self, socket, queue):
        """
        异步写入数据
        :param trans:
        :param queue:
        :return:
        """
        msg = queue.get()
        while msg is not None:
            try:
                # print "====> ", msg
                socket.write(msg)
                socket.flush()
            except:
                print_exception(info_logger)
                break

            # 简单处理
            if not self.alive:
                break
            msg = queue.get()
        if msg is None:
            info_logger.warning("....Worker Connection To LB Failed, LoopRead Stop")


    def prepare_exit(self):
        # 1. 当前的readloop结束之后就不再注册
        self.alive = False

        if not self.queue:
            return

        self.queue.put(new_rpc_exit_message())

        # 过一会应该就没有新的消息过来了
        start = time.time()
        while self.queue:
            now = time.time()
            if now - self.last_request_time > 5:
                info_logger.warning("[%s]Grace Exit of Worker", self.service)
                exit(0)
            else:
                info_logger.warning("[%s]Waiting Exit of Worker, %.2fs", self.service, now - start)
                time.sleep(1)


    def run(self):
        import gevent.monkey

        gevent.monkey.patch_socket()

        # 0. 注册信号(控制运维)
        self.init_signal()

        # 2. 监听数据
        # self.loop_reader()
        self.acceptor_task = gevent.spawn(self.loop_all)

        # 3. 等待结束
        try:
            self.acceptor_task.get()
        finally:
            self.stop()
            self.task_pool.join(raise_error=True)

    def stop(self):
        if self.acceptor_task is not None:
            self.acceptor_task.kill()
            self.acceptor_task = None

    def init_signal(self):
        def handle_term(*_):
            info_logger.warning(Fore.RED + "Receive Exit Signal" + Fore.RESET)
            self.prepare_exit()


        # 2/15
        signal.signal(signal.SIGINT, handle_term)
        signal.signal(signal.SIGTERM, handle_term)

        info_logger.warning(Fore.RED + "To graceful stop current worker plz. use:" + Fore.RESET)
        info_logger.warning(Fore.GREEN + ("kill -15 %s" % os.getpid()) + Fore.RESET)