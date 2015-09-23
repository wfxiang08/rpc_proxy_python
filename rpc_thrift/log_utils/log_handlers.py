# -*- coding:utf-8 -*-
import logging
import os
from stat import ST_DEV, ST_INO


class CustomWatchedFileHandler(logging.FileHandler):
    """
        配合logrotate(https://git.chunyu.me/feiwang/logrotate),
        监听log文件的大小的变化
    """
    def __init__(self, filename, mode='a', encoding=None, delay=0):
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)
        if not os.path.exists(self.baseFilename):
            self.dev, self.ino = -1, -1
        else:
            stat = os.stat(self.baseFilename)
            self.dev, self.ino = stat[ST_DEV], stat[ST_INO]

    def emit(self, record):
        if not os.path.exists(self.baseFilename):
            stat = None
            changed = 1
        else:
            stat = os.stat(self.baseFilename)
            # http://pubs.opengroup.org/onlinepubs/009695399/basedefs/sys/stat.h.html
            # The st_ino and st_dev fields taken together uniquely identify the file within the system.
            changed = (stat[ST_DEV] != self.dev) or (stat[ST_INO] != self.ino)

        if changed and self.stream is not None:
            # 打开文件可能出错，因此每次判定是否已经关闭
            if not self.stream.closed:
                self.stream.flush()
                self.stream.close()

            # 重新打开文件
            self.stream = self._open()
            if stat is None:
                stat = os.stat(self.baseFilename)

            self.dev, self.ino = stat[ST_DEV], stat[ST_INO]

        # 交给系统默认的实现
        print "Record: ..."
        logging.FileHandler.emit(self, record)


class KidsLogHandler(logging.Handler):
    """
        基于Kids的日志处理, 在django settings中配置如下:

        首先添加:
            1. redis 配置项，本机 kids agent 的redis接口，并非真正的 redis
            'redis_kids': {
                'host': 'localhost',
                'port': '3388',
                'password': None,
            }
            2. log handler 配置项
            'kids_logger': {
                'level': 'INFO',
                'class': 'medweb_utils.log.log_handler.KidsLogHandler',
                'formatter': 'verbose',
                'topic': 'medweb',  # 和产品相关，例如: medweb, medweb_test, medweb_pub, 不同的产品的日志会放置在不同的地方
                'redis': 'redis_kids'
            }
        然后为对应的Logger的Handlers中添加: kids_logger, 例如:
        'elapsed_logger': {
            'handlers': ['elapsed_logger', 'kids_logger'],
            'level': 'INFO',
            'propagate': False,
        }


        最终:
            log会以
                TOPIC.LOGGER作为最终的topic交给kid agent, 然后 kids server, 最后kids server将它们放在不同的文件夹中

        Log服务的规划参考: https://git.chunyu.me/op/chunyu_kids

    """
    def __init__(self, redis, topic='', level=logging.NOTSET):
        super(KidsLogHandler, self).__init__(level)
        self.topic = topic or 'default'
        self.redis_conf_name = redis
        self.kids_redis = None

    def get_kids(self):
        """
        具体的项目需要实现该函数
        """
        # from settings import REDIS
        # redis_kids = REDIS["redis_kids"]
        # self.kids_redis = get_redis_client_from_hostport(redis_kids["host"], redis_kids["port"])
        return None

    def emit(self, record):

        # 延后加载redis, 防止循环依赖
        if not self.kids_redis:
            self.kids_redis = self.get_kids()

        try:
            msg = self.format(record)
            if isinstance(msg, unicode):
                msg = msg.encode("utf-8")
            self.kids_redis.publish(self.topic + "." + record.name, msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)