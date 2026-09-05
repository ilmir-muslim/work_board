# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

project_root = Path.cwd().resolve()

# Данные (папки с файлами)
datas = []
for d in ['templates', 'static', 'media']:
    src = project_root / d
    if src.exists():
        datas.append((str(src), d))

# База данных
db_path = project_root / 'db.sqlite3'
if db_path.exists():
    datas.append((str(db_path), '.'))

# Пакеты Python (копируем как есть, они будут добавлены в sys.path через runtime_hook)
for pkg in ['config', 'core', 'developers', 'managers', 'users']:
    src = project_root / pkg
    if src.exists():
        datas.append((str(src), pkg))

a = Analysis(
    ['desktop_app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Базовые django
        'django',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        # Whitenoise
        'whitenoise',
        'whitenoise.middleware',
        'whitenoise.runserver_nostatic',
        'whitenoise.storage',
        # WSGI и сервер разработки
        'django.core.handlers.wsgi',
        'django.core.servers.basehttp',
        'django.core.management.commands.runserver',
        # Конфиг
        'config',
        'config.settings',
        'config.wsgi',
        'config.urls',
        'config.asgi',
        # Приложения (перечисляем все подмодули, которые есть в каждом)
        'core',
        'core.apps',
        'core.models',
        'core.views',
        'core.admin',
        'core.context_processors',

        'developers',
        'developers.apps',
        'developers.models',
        'developers.views',
        'developers.admin',
        'developers.api',
        'developers.forms',
        'developers.urls',

        'managers',
        'managers.apps',
        'managers.models',
        'managers.views',
        'managers.admin',
        'managers.api',
        'managers.forms',
        'managers.urls',

        'users',
        'users.apps',
        'users.models',
        'users.views',
        'users.admin',
        'users.forms',
        'users.urls',

        # Middleware компоненты (могут понадобиться)
        'django.middleware.security',
        'django.middleware.common',
        'django.middleware.csrf',
        'django.middleware.clickjacking',
        'django.contrib.auth.middleware',
        'django.contrib.messages.middleware',
        'django.contrib.sessions.middleware',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='workboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)