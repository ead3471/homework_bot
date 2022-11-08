from dotenv import load_dotenv
import os
from telegram import Bot
import time
import requests
from pprint import pprint

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


def send_message(bot, message):
    ...


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    ...


def check_response(response):

    ...


def parse_status(homework):
    homework_name = ...
    homework_status = ...

    ...

    verdict = ...

    ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    ...


def main():
    """Основная логика работы бота."""

   

    # bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    print(PRACTICUM_TOKEN)
   

    while True:
        try:
            params={'from_date': 0}
            response = requests.get(ENDPOINT, headers=HEADERS, params=params)

            current_timestamp = int(time.time())
            pprint(response.json())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'

            time.sleep(RETRY_TIME)
        else:
            pass
            


if __name__ == '__main__':
    main()