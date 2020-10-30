import logging

__all__ = [
    # platform log
    'default_logger',
    'task_logger',
    'sys_logger',
    'custom_logger',
]

default_logger = logging.getLogger('default')
task_logger = logging.getLogger('task')
sys_logger = logging.getLogger('syslog')


def custom_logger(logger_name):
    return logging.getLogger(logger_name)
