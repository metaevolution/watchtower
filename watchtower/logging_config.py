import functools
import logging
import os
from logging.handlers import RotatingFileHandler

from .util import Color

os.makedirs("logs") if not os.path.exists("logs") else None


class CustomFormatter(logging.Formatter):
    reset = "\x1b[0m"
    log_format = "%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: Color.F_DarkGray + log_format + reset,
        logging.INFO: Color.F_Default + log_format + reset,
        logging.WARNING: Color.F_Yellow + log_format + reset,
        logging.ERROR: Color.F_Red + log_format + reset,
        logging.CRITICAL: Color.F_BoldRed + log_format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler_debug = RotatingFileHandler(
    "logs/debug.log", maxBytes=1000000, backupCount=5
)
file_handler_debug.setLevel(logging.DEBUG)
formatter_debug = logging.Formatter("%(asctime)s - %(name)s - DEBUG - %(message)s")
file_handler_debug.setFormatter(formatter_debug)

file_handler_error = RotatingFileHandler(
    "logs/error.log", maxBytes=1000000, backupCount=5
)
file_handler_error.setLevel(logging.ERROR)
formatter_error = logging.Formatter("%(asctime)s - %(name)s - ERROR - %(message)s")
file_handler_error.setFormatter(formatter_error)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
# formatter_console = logging.Formatter("[%(levelname)s] %(message)s")
console_handler.setFormatter(CustomFormatter())

logger.addHandler(file_handler_debug)
logger.addHandler(file_handler_error)
logger.addHandler(console_handler)


def log_wrapper(func):
    def _wrapper(*args, **kwargs):
        logger.debug("BEFORE '%s' args: '%s' kwargs: '%s'", func, args, kwargs)

        out = func(*args, **kwargs)

        logger.debug("AFTER %s", func)
        return out

    return _wrapper


def update_console_level(level):
    console_handler.setLevel(level)


def func_logger(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"func: {func}, args:{args}, kwargs:{kwargs}")
        result = func(*args, **kwargs)
        # logger.debug(f"results:{result}")
        return result

    return wrapper
