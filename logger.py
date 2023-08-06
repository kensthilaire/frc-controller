import logging
import logging.handlers

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger('MyLogger')
logger.setLevel(logging.INFO)

handler = logging.handlers.SysLogHandler(address = '/dev/log')
logger.addHandler(handler)

