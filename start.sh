#!/bin/bash

echo "🔄 Запускаем бота..."

# Проверка наличия python3
if ! command -v python3 &> /dev/null
then
    echo "❌ Ошибка: Python3 не установлен или не найден в PATH."
    exit 1
fi

# Запуск бота и логирование ошибок (если есть)
python3 bot.py 2> error.log

# Проверка, завершился ли бот с ошибкой
if [ $? -ne 0 ]; then
    echo "⚠️ Бот завершился с ошибкой. Подробности в error.log"
else
    echo "✅ Бот успешно запущен."
fi
