# -*- coding: utf-8 -*-
from __future__ import absolute_import

import collections
import logging
import os
import signal
import time
import traceback

from colorama import Fore
import gevent.pool
import gevent.queue
import gevent.event
import gevent.local
import gevent.lock
from rpc_thrift.cython.cybinary_protocol import TCyBinaryProtocol
from thrift.Thrift import TApplicationException, TMessageType
from thrift.transport.TSocket import TSocket
from thrift.transport.TTransport import TTransportException
from rpc_thrift.cython.cyframed_transport_ex import TCyFramedTransportEx

from rpc_thrift.cython.cymemory_transport import TCyMemoryBuffer

from rpc_thrift import MESSAGE_TYPE_HEART_BEAT
from rpc_thrift.config import print_exception
from rpc_thrift.heartbeat import new_rpc_exit_message

info_logger = logging.getLogger('info_logger')
exception_logger = logging.getLogger('exception_logger')

ISOTIMEFORMAT='%Y-%m-%d %X'

class RpcWorker(object):
    def __init__(self, processor, address, pool_size=1, service=None, fastbinary=False):
        self.processor = processor

        self.pid = os.getpid() # 记录当前进程的Id

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
        self.connection_ok = True
        self.alive = True
        self.reconnect_interval = 1

        self.responses = []

        self.service = service
        self.queue = None
        self.socket = None
        self.last_request_time = 0
        self.last_hb_time = 0
        self.out_protocols = collections.deque()

    def handle_request(self, proto_input, queue, request_meta):
        """
            从 proto_input中读取数据，然后调用processor处理请求，结果暂时缓存在内存中, 最后一口气交给 queue,
            由专门的 greenlet将数据写回到socket上
            request_meta = (name, type, seqid, start_time)
        """
        start_time0 = time.time()
        # 1. 获取一个可用的trans_output
        if len(self.out_protocols) > 0:
            trans_output, proto_output = self.out_protocols.popleft()
            trans_output.prepare_4_frame() # 预留4个字节的Frame Size
        else:
            trans_output = TCyMemoryBuffer()
            trans_output.prepare_4_frame()
            proto_output = TCyBinaryProtocol(trans_output, client=False) # 无状态的


        try:
            # 2.1 处理正常的请求
            self.processor.process(proto_input, proto_output)
            queue.put(trans_output)

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
            queue.put(trans_output)

        finally:
            start_time = request_meta[3]
            now = time.time()
            elapsed = now - start_time
            if elapsed > 2:
                # 做异常记录
                exception_logger.info("Exception Request: %s %s seqId: %s_%s, Elaspsed: %.3f, Execute: %.3f", request_meta[0], request_meta[1], self.pid, request_meta[2], elapsed, now - start_time0)

            # 3. 回收 transport 和 protocol
            self.out_protocols.append((trans_output, proto_output))


    def loop_all(self):

        while self.alive:
            # 一次只有一个连接
            self.connection_to_lb()

    def connection_to_lb(self):
        if self.unix_socket:
            info_logger.info("Prepare open a socket to lb: %s, pid: %s", self.unix_socket, self.pid)
        else:
            info_logger.info("Prepare open a socket to lb: %s:%s, pid: %s", self.host, self.port, self.pid)

        # 1. 创建一个到lb的连接，然后开始读取Frame, 并且返回数据
        socket = TSocket(host=self.host, port=self.port, unix_socket=self.unix_socket)

        try:
            if not socket.isOpen():
                socket.open()
            socket.setTimeout(5000) # 出现异常，会自己重启
        except TTransportException:
            info_logger.info("Sleep %ds for another retry, pid: %s", self.reconnect_interval, self.pid)
            time.sleep(self.reconnect_interval)
            print_exception(info_logger)

            if self.reconnect_interval < 4:
                self.reconnect_interval *= 2
            return

        # 2. 连接创建成功
        self.reconnect_interval = 1

        self.socket = socket

        # 每次建立连接都重新构建
        self.queue = gevent.queue.Queue()
        self.connection_ok = True

        info_logger.info("Begin request loop....")
        # 3. 在同一个transport上进行读写数据
        transport = TCyFramedTransportEx(socket)

        #
        # 关注 transport的接口:
        #      flush_frame_buff
        #      read_frame
        #
        g1 = gevent.spawn(self.loop_reader, transport, self.queue)
        g2 = gevent.spawn(self.loop_writer, transport, self.queue)
        g3 = gevent.spawn(self.loop_hb_detect, transport)
        gevent.joinall([g1, g2, g3])


        # 4. 关闭连接
        try:
            # 什么情况下会关闭呢? 连接断开了,
            print time.strftime(ISOTIMEFORMAT, time.localtime()), "Trans Closed, queue size: ", self.queue.qsize(), ", pid: ", self.pid
            self.queue = None
            self.socket = None
            transport.close() # 关闭transport(而且transport也不会继续复用)
        except:
            print_exception(info_logger)
            pass


    def loop_hb_detect(self, transport):
        self.last_hb_time = time.time()
        while transport.isOpen(): # 关闭socket之后, transport也就关闭了
            # 如果5s内没有心跳，则关闭当前的transport
            if time.time() - self.last_hb_time > 5:
                print time.strftime(ISOTIMEFORMAT, time.localtime()), " heartbeat lost, close transport, pid: ", self.pid
                transport.close()
                break
            else:
                gevent.sleep(2)

    def loop_reader(self, transport, queue):
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
        # transport = TCyFramedTransport(None)

        while self.connection_ok:
            try:
                # 1. 读取一帧数据
                trans_input = transport.read_frame() # TCyMemoryBuffer, 有可能一直堵在这里, 通过 loop_hb_detect.close()来终止

                trans_input.reset_frame() # 跳过Frame Size
                proto_input = TCyBinaryProtocol(trans_input, client=False)

                name, type, seqid = proto_input.readMessageBegin()


                # 如果是心跳，则直接返回
                if type == MESSAGE_TYPE_HEART_BEAT:
                    trans_input.reset()
                    queue.put(trans_input)
                    self.last_hb_time = time.time()
                    # print "Received Heartbeat Signal........"
                    continue

                else:
                    self.last_request_time = time.time()

                    # print "Read Request"
                    trans_input.reset_frame()
                    self.task_pool.spawn(self.handle_request, proto_input, queue, (name, type, seqid, time.time()))
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


    def loop_writer(self, transport, queue):
        """
        异步写入数据
        :param trans:
        :param queue:
        :return:
        """
        msg = queue.get()
        # msg 为 None表示已经读取完毕所有的 input message
        while self.connection_ok and (msg is not None):
            # print "Write Back Msg"
            try:
                transport.flush_frame_buff(msg)
            except:
                print_exception(info_logger)
                self.connection_ok = False
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
                # time.sleep(1)
                gevent.sleep(1)


    def run(self):
        import gevent.monkey

        # gevent.monkey.patch_socket()
        gevent.monkey.patch_all()

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