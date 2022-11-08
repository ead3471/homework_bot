from dotenv import load_dotenv
import os
from telegram import Bot, TelegramError
import time
import requests
from pprint import pprint
import logging
from exceptions import BadAPIResponseCode
from loggers import TelegramBotLogger

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_TIME = 5
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger:logging.Logger = logging.getLogger()


def init_logger(logging_level:int, )->logging.Logger:
    """Logging initialization"""
    os.makedirs('logs', exist_ok=True)
    logger = logging.getLogger('main_logger')
    logger.setLevel(logging_level)
    formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s')
    file_handler = logging.FileHandler(filename='logs/main.log', mode='w')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging_level)
    
    stream_handler =logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging_level)


    telegram_logger = TelegramBotLogger(logging_level,Bot(token=TELEGRAM_TOKEN),123)
    telegram_logger.setFormatter(formatter)


    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.addHandler(telegram_logger)
    return logger


def send_message(bot:Bot, message:str):
    """Send message to the end user(user defined by TELEGRAM_CHAT_ID env parameter)"""
    try:
        logger.info(f"Send message to {TELEGRAM_CHAT_ID}:{message}")
        bot.send_message(text=message, chat_id=TELEGRAM_CHAT_ID)
        logger.info("Message sent")
    except TelegramError as error:
        logger.error(f'Sending message error:{error}')

def get_api_answer(current_timestamp)->dict:
    """Get homework status info"""
    timestamp = current_timestamp or int(time.time())
    logger.debug(f"Process request to yandex API. timestamp={timestamp}")
    params = {'from_date': timestamp}
    try:
        requests.get(ENDPOINT, headers=HEADERS, params=params).json()
    except requests.exceptions.RequestException as error:
        logger.error(f"Process request error:{error}")
        return None
    else:
        pass




def check_response(response):

    pass

def parse_status(homework):
    # homework_name = ...
    # homework_status = ...

   

    # verdict = ...

    

    # return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    pass


def check_tokens()->bool:
    """Check required env params: PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID"""
    return bool(PRACTICUM_TOKEN) and bool(TELEGRAM_TOKEN) and bool(TELEGRAM_CHAT_ID)


def main():
    """Основная логика работы бота."""
    logger = init_logger(logging.INFO)

    if check_tokens():
        logger.info("Tokens check ok")
    else:
        logger.critical("Tokens is not set. Bot is stopped")
        return

    try:
        bot = Bot(token=TELEGRAM_TOKEN)
    except Exception as error:
        logging.error(f'Bot init error:{error}')
        return

    send_message(bot,"Test")
    logger.critical("TTTT")
    current_timestamp = int(time.time())
    return

    while True:
        try:
            params={'from_date': 0}
            # response = 

            current_timestamp = int(time.time())
            pprint(response.json())
            time.sleep(RETRY_TIME)

        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            
        else:
            pass
        finally:
            time.sleep(RETRY_TIME)
            


if __name__ == '__main__':
    main()
