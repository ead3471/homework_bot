import logging
from telegram import Bot
import os


class TelegramBotLogger(logging.Handler):
    def __init__(self, level: int, bot:Bot, chat_id) -> None:
        super().__init__(level)
        self.bot = bot
        self.chat_id = chat_id
        self.init_logger(level)

    def init_logger(self, logger_level:int):
        os.makedirs('logs', exist_ok=True)
        self.internal_logger = logging.getLogger('logger')
        formatter = logging.Formatter('%(asctime)s,%(levelname)s, %(message)s')
        file_handler = logging.FileHandler(filename='logs/logger.log', mode='w')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logger_level)
        self.internal_logger.addHandler(file_handler)

    
    def emit(self, record):
        msg:str = self.format(record)
        for error_level in ['INFO', 'DEBUG', 'ERROR', 'CRITICAL']:
            if error_level in msg:
                msg=msg.replace(error_level, f'<u><b>{error_level}</b></u>')
                break

        try:
            self.bot.send_message(chat_id = self.chat_id,text=msg)
        except Exception as exception:
            self.internal_logger.critical(f'Log to telegram(chat_id={self.chat_id}) error:{exception}')

