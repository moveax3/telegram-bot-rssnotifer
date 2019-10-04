import logging
import threading
import coloredlogs
from logging import Handler

from common import send_logs_for_admins


class TelegramHandler(Handler):
    def emit(self, record):
        log_entry = self.format(record)
        send_thread = threading.Thread(target=send_logs_for_admins, args=(log_entry,))
        send_thread.start()


def get_logger(name: str) -> object:
    coloredlogs.install()
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    telegram_handler = TelegramHandler()
    formatter = logging.Formatter("[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")
    stream_handler.setFormatter(formatter)
    telegram_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(telegram_handler)
    return logger
