#!/usr/bin/env python3
import os
import sys
import threading
import time
from pathlib import Path

# Добавляем текущую папку в путь (для запуска из исходников)
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.core.management import call_command
from django.db import connections
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import QUrl, QTimer, Qt
from PySide6.QtWebEngineWidgets import QWebEngineView

server_running = False


def start_django_server():
    global server_running
    print("Запуск Django сервера на http://127.0.0.1:8000")
    try:
        call_command("runserver", "127.0.0.1:8000", use_reloader=False, verbosity=1)
        server_running = True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Ошибка запуска сервера: {e}")
        server_running = False


def stop_django_server():
    for conn in connections.all():
        conn.close()
    print("Сервер Django остановлен")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WorkBoard - Учёт времени")
        self.resize(1200, 800)
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        self.check_server_and_load()

    def check_server_and_load(self):
        import urllib.request
        import urllib.error

        try:
            with urllib.request.urlopen("http://127.0.0.1:8000", timeout=0.5):
                self.browser.load(QUrl("http://127.0.0.1:8000"))
        except (urllib.error.URLError, ConnectionRefusedError):
            QTimer.singleShot(500, self.check_server_and_load)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Выход",
            "Закрыть приложение?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            stop_django_server()
            time.sleep(0.5)
            event.accept()
        else:
            event.ignore()


def run_gui():
    app = QApplication(sys.argv)
    # Убираем deprecated строку
    # app.setAttribute(Qt.AA_UseHighDpiPixmaps)  # закомментировано
    window = MainWindow()
    window.show()
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    thread = threading.Thread(target=start_django_server, daemon=True)
    thread.start()
    time.sleep(1.5)
    exit_code = run_gui()
    stop_django_server()
    sys.exit(exit_code)
