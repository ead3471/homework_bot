from datetime import datetime
from dotenv import load_dotenv
import os
from telegram import Bot, TelegramError
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
import time
import requests
import logging
from exceptions import (BadAPIHttpResponseCode,
                        APIRequestProcessingError,
                        APIError,
                        BadAPIResponseFormat)
from loggers import TelegramBotLogger
from http import HTTPStatus
from json import JSONDecodeError
from schema import Schema, SchemaError
from telegram.ext import Updater, CommandHandler

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

LOG_LEVEL = os.getenv('LOG_LEVEL') or logging.INFO
TELEGRAM_LOG_LEVEL = os.getenv('TELEGRAM_LOG_LEVEL') or logging.ERROR


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger: logging.Logger = logging.getLogger(__name__)


last_update_timestamp = int(time.time())


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
    logger.info(f"Log inited. Logging level={logging_level}")


def init_telegram_logger(logging_level):
    """Initializing the logger, which sends error messages to the user."""
    logger = logging.getLogger(__name__)
    formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s')
    telegram_logger = TelegramBotLogger(logging_level,
                                        Bot(token=TELEGRAM_TOKEN),
                                        TELEGRAM_CHAT_ID)
    telegram_logger.setFormatter(formatter)
    logger.addHandler(telegram_logger)
    logger.info(f"Telegram Log inited. Logging level={logging_level}")


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
    params = {'from_date': timestamp}
    timestamp_str = datetime.fromtimestamp(timestamp)
    try:
        logger.info(
            ("Sending request to yandex API. "
             f"timestamp={timestamp}({timestamp_str})"))
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        logger.info(f'Data received:{response.json()}')
        if response.status_code == HTTPStatus.OK:
            result = response.json()
            if 'error' in result:
                raise APIError(f"Error at API response: {result.get('error')}")
        else:
            raise BadAPIHttpResponseCode(
                ("Bad response code from"
                 f"yandex API recieved:{response.status_code}"))
    except requests.exceptions.RequestException as error:
        raise APIRequestProcessingError(f"Process request error:{error}")
    except JSONDecodeError or ValueError as error:
        raise BadAPIResponseFormat(f'API response format error:{error}')
    return result


def check_response(response: dict) -> list:
    """Check and validate response from API."""
    logger.info("Checking the received data")

    if type(response) is not dict:
        raise TypeError(f"Response is not a dict:{type(response)}")

    if 'current_date' not in response or 'homeworks' not in response:
        raise BadAPIResponseFormat(("Response must contain 'current_date'"
                                   " and 'homeworks' keys"))

    if type(response['homeworks']) is not list:
        raise TypeError("Homeworks is not a list")

    raw_homeworks = response['homeworks']
    homeworks = []
    if raw_homeworks:
        logger.info(f'Recieved data contain {len(raw_homeworks)} records.')
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
                logger.error(
                    f'Wrong homework data format:{error} at {homework}')
        logger.info(f'The resulting list contains {len(homeworks)} items')
        return homeworks
    else:
        logger.info('Response homworks list is empty')


def parse_status(homework: str) -> str:
    """Pasrse API repsponse and return given homework status."""
    logger.info(f"Parse homework status for {homework}")
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]

    logger.info((f"{homework_name} status is changed! "
                f"New status is '{homework['status']}',"
                 f" updated at {homework['date_updated']})"))
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Check required env params."""
    logger.info("Tokens checking")
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


def start(update: Update, context: CallbackContext):
    """Starting command callback."""
    logger.info('Starting to check the status of homework')
    send_message(context.bot, "Starting to check the status of homework")
    context.job_queue.run_repeating(check_homeworks,
                                    RETRY_TIME,
                                    context=update.message.chat_id)


def check_homeworks(context: CallbackContext):
    """Main check homeworks status function."""
    global last_update_timestamp
    try:
        response = get_api_answer(last_update_timestamp)
        homeworks = check_response(response)
        if homeworks:
            for homework in homeworks:
                send_message(context.bot, parse_status(homework))

        last_update_timestamp = response.get('current_date',
                                             last_update_timestamp)
    except Exception as error:
        logger.exception(f'Failed to retrieve homework status data: {error}')


def stop(update: Update, context: CallbackContext):
    """Stoping command callback."""
    context.job_queue.stop()


def main():
    """Основная логика работы бота."""
    init_logger(LOG_LEVEL)

    if check_tokens():
        logger.info('Tokens check completed')
        init_telegram_logger(TELEGRAM_LOG_LEVEL)
    else:
        logger.critical("Tokens are not set. The bot is stopped")
        return

    try:
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        updater.dispatcher.add_handler(CommandHandler('start', start))
        updater.dispatcher.add_handler(CommandHandler('stop', stop))
        updater.start_polling()
        updater.idle()
    except Exception as exception:
        logger.critical(f"Error at bot startup:{exception}")


if __name__ == '__main__':
    main()
