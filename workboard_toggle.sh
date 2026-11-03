#!/bin/bash
PROJECT_DIR="/home/ilmir/dev_code/pet_project/work_board_dev/work_board"
cd "$PROJECT_DIR" || exit 1

if docker compose ps --services --filter "status=running" | grep -q "^web$"; then
    kdialog --passivepopup "🛑 Остановка сервера..." 3
    docker compose stop
    kdialog --passivepopup "✅ Сервер остановлен!" 5
else
    kdialog --passivepopup "🚀 Запуск сервера..." 3
    docker compose up -d --build
    kdialog --passivepopup "✅ Готово! Можно обновлять страницу." 5
fi