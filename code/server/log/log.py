import logging
import sys


APP_LOGGER_NAME = "Guka_Server"


def setup_log(logger_name=APP_LOGGER_NAME, file_name=None):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.WARNING)
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(filename)s[line:%(lineno)d] |  %(levelname)s: %(message)s |  %(funcName)s"
    )
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(sh)
    if file_name:
        fh = logging.FileHandler(file_name)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger
def get_log(module_name):
    return logging.getLogger(APP_LOGGER_NAME).getChild(module_name)

# logging.debug('debug，用来打印一些调试信息，级别最低')
# logging.info('info，用来打印一些正常的操作信息')
# logging.warning('waring，用来用来打印警告信息')
# logging.error('error，一般用来打印一些错误信息')
# logging.critical('critical，用来打印一些致命的错误信息，等级最高')
