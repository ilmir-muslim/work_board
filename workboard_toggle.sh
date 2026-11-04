#!/bin/bash

# Абсолютный путь к проекту
PROJECT_DIR="/home/ilmir_pc/dev_code/pet_project/work_board_dev/work_board"
cd "$PROJECT_DIR" || exit

# Проверяем, запущен ли контейнер web
if docker compose ps --status running | grep -q "web"; then
    # Если работает — останавливаем
    notify-send "WorkBoard" "🛑 Остановка сервера..." --icon=dialog-information
    docker compose stop
    notify-send "WorkBoard" "✅ Сервер остановлен!" --icon=dialog-information
else
    # Если не работает — запускаем
    notify-send "WorkBoard" "🚀 Запуск сервера..." --icon=dialog-information
    docker compose up -d
    notify-send "WorkBoard" "✅ Готово! Можно обновлять страницу в браузере." --icon=dialog-information
fi