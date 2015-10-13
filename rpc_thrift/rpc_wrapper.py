# -*- coding: utf-8 -*-
from __future__ import absolute_import
import time
import traceback
from rpc_thrift.services.ttypes import RpcException

# log_func
# def log_func(*args, **kwargs, result = None, ex = None, trace=None):
#
#
def rpc_wrapper_for_class_method(info_logger, arg_format=None):
    """
    计算类成员函数的执行时间&异常处理, 使用方法(其中logger可以为None)
        @calculate_class_fun_execute_time(logger)
        def processs_method(self, param1):
            xxx
    """
    def wrapper(func):
        def _calculate_time(*args, **kwargs):
            try:
                if info_logger:
                    t = time.time()

                    # rpc调用中没有kwargs
                    result = func(*args, **kwargs)

                    t = (time.time() - t) * 1000
                    if arg_format:
                        args_str = arg_format(*args[1:])
                    else:
                        args_str = ", ".join(map(str, args[1:]))
                    info_logger.info('\033[32m%s\033[39m(%s), Elapsed: %.2fms' % (func.__name__, args_str, t))
                else:
                    result = func(*args, **kwargs)
                return result
            except Exception as e:
                if arg_format:
                    args_str = arg_format(*args[1:])
                else:
                    args_str = ", ".join(map(str, args[1:]))
                raise RpcException(0, '%s(%s), Exception: %s, Trace: %s' % (func.__name__, args_str, str(e), traceback.format_exc()))

        return _calculate_time
    return wrapper



def rpc_wrapper_for_method(info_logger, arg_format=None):
    """
    计算普通函数的执行时间&异常处理, 使用方法(其中logger可以为None)
        @calculate_class_fun_execute_time(logger)
        def processs_method(self, param1):
            xxx
    """
    def wrapper(func):
        def _calculate_time(*args, **kwargs):
            try:
                if info_logger:
                    t = time.time()
                    result = func(*args, **kwargs)
                    t = (time.time() - t) * 1000
                    if arg_format:
                        args_str = arg_format(*args)
                    else:
                        args_str = ", ".join(map(str, args))
                    info_logger.info('\033[32m%s\033[39m(%s), Elapsed: %.4fms' % (func.__name__, args_str, t))
                else:
                    result = func(*args, **kwargs)
                return result
            except Exception as e:
                if arg_format:
                    args_str = arg_format(*args)
                else:
                    args_str = ", ".join(map(str, args))
                raise RpcException(0, '%s(%s), Exception: %s, Trace: %s' % (func.__name__, args_str, str(e), traceback.format_exc()))

        return _calculate_time
    return wrapper
