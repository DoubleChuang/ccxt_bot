# -*- coding: utf-8 -*-

import logging
import logging.config
import sys

APP_NAME = "cctx_bot"
ROOT_LOG_NAME = f"{APP_NAME}.root"
ERROR_LOG_NAME = f"{APP_NAME}.error"

LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "loggers": {
        ROOT_LOG_NAME: {"level": "INFO", "handlers": ["console"]},
        ERROR_LOG_NAME: {
            "level": "INFO",
            "handlers": ["error_console"],
            "propagate": True,
            "qualname": ERROR_LOG_NAME,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": sys.stdout,
        },
        "error_console": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": sys.stderr,
        },
    },
    "formatters": {
        "generic": {
            # "format": "%(asctime)s [%(levelname)s] %(message)s",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
    },
}

logging.config.dictConfig(LOGGER_CONFIG)

logger = logging.getLogger(ROOT_LOG_NAME)
error_logger = logging.getLogger(ERROR_LOG_NAME)
