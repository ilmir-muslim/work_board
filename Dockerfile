FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# uv: ставим пакеты в системный Python (venv в контейнере не нужен)
ENV UV_SYSTEM_PYTHON=1
# uv: отключаем кэш, чтобы образ не раздувался
ENV UV_NO_CACHE=1

WORKDIR /app

# ffmpeg нужен для pydub/whisper, gcc/libpq-dev — для сборки пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Ставим uv внутрь образа
RUN pip install --no-cache-dir uv

COPY requirements.txt .

# 1. Сначала CPU-версия PyTorch — блокирует CUDA-зависимости NVIDIA
RUN uv pip install torch torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# 2. Потом остальные пакеты (whisper увидит уже установленный CPU-torch)
RUN uv pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "300"]