#!/bin/bash

pip install python-telegram-bot==20.3
pip install requests==2.31.0
pip install python-dotenv==1.0.1
pip install openai==1.14.1
pip install google-cloud-texttospeech==2.14.1

echo "🔄 Запускаем бота..."

if ! command -v python3 &> /dev/null
then
    echo "❌ Ошибка: Python3 не установлен или не найден в PATH."
    exit 1
fi

python3 soulmuse-bot/webhook_bot.py
