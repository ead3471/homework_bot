from dotenv import load_dotenv
import os
from telegram import Bot, TelegramError
import time
import requests
import logging
from exceptions import (BadAPIHttpResponseCode,
                        APIRequestProcessingError,
                        APIError,
                        BadAPIResponseFormat,
                        UncknownError)
from loggers import TelegramBotLogger
from http import HTTPStatus
from json import JSONDecodeError
from schema import Schema, SchemaError

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


logger: logging.Logger = logging.getLogger(__name__)


homeworks_previous_data = {}


def init_logger(logging_level: int) -> logging.Logger:
    """Logging initialization."""
    os.makedirs('logs', exist_ok=True)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging_level)
    formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s')
    file_handler = logging.FileHandler(filename='logs/main.log', mode='w')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging_level)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging_level)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def init_telegram_logger(logging_level):
    """Initializing the logger, which sends error messages to the user."""
    logger = logging.getLogger(__name__)
    formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s')
    telegram_logger = TelegramBotLogger(logging_level,
                                        Bot(token=TELEGRAM_TOKEN),
                                        TELEGRAM_CHAT_ID)
    telegram_logger.setFormatter(formatter)
    logger.addHandler(telegram_logger)


def send_message(bot: Bot, message: str):
    """Send message to the end user."""
    try:
        logger.info(f"Send message to {TELEGRAM_CHAT_ID}:{message}")
        bot.send_message(text=message, chat_id=TELEGRAM_CHAT_ID)
        logger.info("Message sent")
    except TelegramError as error:
        logger.error(f'Sending message error:{error}')


def get_api_answer(current_timestamp: int = None) -> dict:
    """Get homework status info."""
    timestamp = current_timestamp or int(time.time())
    logger.info(f"Process request to yandex API. timestamp={timestamp}")
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        logger.info('Data recieved')
        if response.status_code == HTTPStatus.OK:
            result = response.json()
            if 'error' in result:
                raise APIError(f"Error at API response: {result.get('error')}")
        else:
            raise BadAPIHttpResponseCode(("Bad response code from"
                                         f"yandex API:{response.status_code}"))
    except requests.exceptions.RequestException as error:
        raise APIRequestProcessingError(f"Process request error:{error}")
    except JSONDecodeError or ValueError as error:
        raise BadAPIResponseFormat(f'API response format error:{error}')
    except Exception as error:
        raise UncknownError(f'Uncknown error:{error}')
    return result


def check_response(response: dict) -> list:
    """Check and validate response from API."""
    if type(response) is not dict:
        raise TypeError("Response is not a dict")

    if 'current_date' not in response or 'homeworks' not in response:
        raise BadAPIResponseFormat(("Response should contain 'current_date'"
                                   " and 'homeworks' keys"))

    if type(response['homeworks']) is not list:
        raise TypeError("Homeworks is not a list")

    raw_homeworks = response['homeworks']
    homeworks = []
    if raw_homeworks:
        schema = Schema({'date_updated': str,
                        'homework_name': str,
                         'id': int,
                         'lesson_name': int,
                         'reviewer_comment': str,
                         'status': str
                         })

        for homework in raw_homeworks:
            try:
                schema.is_valid(homework)
                homeworks.append(homework)
            except SchemaError as error:
                logger.error(f'Wrong homework data format:{error}')
        return homeworks


def parse_status(homework: dict) -> str:
    """Pasrse API repsponse and return given homewtork status."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]

    status_is_changed = (homework_name not in homeworks_previous_data
                         or (homeworks_previous_data['date_updated']
                             != homework['date_updated']))

    if status_is_changed:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Check required env params."""
    result = True
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for name, value in tokens.items():
        if not value:
            logger.critical(f'Token {name} is not set')
            result = False
    return result


def main():
    """Основная логика работы бота."""
    logger = init_logger(logging.DEBUG)

    if check_tokens():
        logger.info('Tokens are loaded')
        init_telegram_logger(logging.ERROR)
    else:
        logger.critical("Tokens is not set. Bot is stopped")
        return

    try:
        bot = Bot(token=TELEGRAM_TOKEN)
    except Exception as error:
        logging.critical(f'Bot init error:{error}')
        return

    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                send_message(bot, check_response(homeworks))

            timestamp = response.get('date_updated', timestamp)
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
