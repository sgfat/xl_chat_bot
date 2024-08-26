import logging
import sys

from logging.handlers import RotatingFileHandler

PHOTO_RETRY_PERIOD = 60 * 60 * 13

# Log format
LOG_DEBUG_FORMAT = '%(asctime)s, %(levelname)s, %(filename)s: %(lineno)d - %(message)s'

# Log file name
LOG_DEBUG_FILE = 'debug.log'

GPT_CONTENT = ('Отвечай по существу, не слишком длинно. '
               'Все ответы должны быть на русском языке. '
               'Форматирование текста подходящее для мессенджера Telegram.')

# Logging settings
logger = logging.getLogger('debug')
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler(sys.stdout)
fileHandler = RotatingFileHandler(LOG_DEBUG_FILE, maxBytes=5000000, backupCount=5)

formatter = logging.Formatter(LOG_DEBUG_FORMAT)

fileHandler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(fileHandler)
logger.addHandler(stream_handler)
