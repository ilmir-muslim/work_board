import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # Запуск из собранного приложения
    base_path = Path(sys._MEIPASS)
    sys.path.insert(0, str(base_path))
    # Устанавливаем переменную окружения для Django
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
