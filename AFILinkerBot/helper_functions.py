import time
import logging
from logging.handlers import RotatingFileHandler

LOG_TIME_FORMAT = "%Y/%m/%d %H:%M:%S "

logger = logging.getLogger("AFILinkerBot Rotating Log")
logger.setLevel(logging.INFO)
    
# add a rotating handler
handler = RotatingFileHandler("AFILinkerBot.log", maxBytes=2048000, backupCount=25)
logger.addHandler(handler)

logger404 = logging.getLogger("AFILinkerBot 404 error Rotating Log")
logger404.setLevel(logging.INFO)
    
# add a rotating handler
handler404 = RotatingFileHandler("404errors.log", maxBytes=2048000, backupCount=25)
logger404.addHandler(handler)

def print_and_log(text, error=False):
    print(text)
    if error:
        logger.error(time.strftime(LOG_TIME_FORMAT) + text)
    else:
        logger.info(time.strftime(LOG_TIME_FORMAT) + text)

def log404(text):
    print(text)
    logger404.info(time.strftime(LOG_TIME_FORMAT) + text)