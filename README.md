### Yandex Practicum homework bot
Telegram bot for tracking the status of homework evaluation on Yandex.Praktikum.
Sends messages when the status changes - taken for review, has remarks, approved.

### Local project deploy
1. Install python 3.11
2. Clone project to your working directory:
    ```
    git@github.com:ead3471/homework_bot.git
    ```
3. Navigate to project directory:
    ```
    cd homework_bot
    ```
4. Сreate virtual environment:
    ```
    python -m venv venv
    ```
5. Activate virtul environment:
    source venv/bin/activate

5. Install requirements:
    ```
    pip install -r requirements.txt
    ```
6. Fill in the .env example file with data and rename it to .env
7. Run bot:
    ```
    python homework_bot.pys
    ```


### Used technologies:
 - requests
 - python-telegram-bot
 - logging
