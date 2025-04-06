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

# Запуск основного Telegram-бота (webhook_bot.py) с логированием ошибок
python3 webhook_bot.py 2>&1 | tee error.log

# Проверка, завершился ли бот с ошибкой
if [ $? -ne 0 ]; then
    echo "⚠️ Бот завершился с ошибкой. Подробности в error.log"
else
    echo "✅ Бот успешно запущен."
fi
