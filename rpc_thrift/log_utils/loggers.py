# -*- coding:utf-8 -*-
from __future__ import  absolute_import
'''
import logging
import os

from rpc_thrift.log_utils.log import dictConfig
from settings import LOGGING

dictConfig(LOGGING)
info_logger = logging.getLogger('info_logger')
'''


'''
settings文件中的配置

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
LOGS_BASE_DIR = os.path.join(PROJECT_ROOT, "log")
if not os.path.exists(LOGS_BASE_DIR):
    os.mkdir(LOGS_BASE_DIR)

LOGGING_CONFIG="rpc_thrift.log_utils.log.dictConfig"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(module)s.%(funcName)s Line:%(lineno)d  %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },

    'handlers': {
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },

        'default': {
            'level': 'INFO',
            'class': 'rpc_thrift.log_utils.log_handlers.CustomWatchedFileHandler',
            'filename': os.path.join(LOGS_BASE_DIR, 'filelog.log'),
            'formatter': 'verbose',
        },
        'info_logger': {
            'level': 'INFO',
            'class': 'rpc_thrift.log_utils.log_handlers.CustomWatchedFileHandler',
            'filename': os.path.join(LOGS_BASE_DIR, 'info_logger.log'),
            'formatter': 'verbose',
        },

        'kids_logger': {
            'level': 'INFO',
            'class': 'rpc_thrift.log_utils.log_handlers.KidsLogHandler',
            'formatter': 'verbose',
            'topic': 'shortmsg',
            'redis': 'redis_kids'
        }
    },

    'loggers': {
        'info_logger': {
            'handlers': ['info_logger'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

logging.root = logging.getLogger('info_logger')

'''