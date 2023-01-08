import logging
import sys

LOGGER_NAME = "test-logger"
LOG_FORMAT = "%(levelname)s - %(asctime)s: %(message)s"
LOG_DATE_FORMAT = "%m/%d/%Y%I:%M:%S %p"


def get_test_logger(log_level: str = logging.DEBUG):
    """get logger, set new one of it doesn't exist"""
    if LOGGER_NAME in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(LOGGER_NAME)
    else:
        logger = logging.getLogger(LOGGER_NAME)
        logger.setLevel(log_level)

        # set handler and formatter
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger