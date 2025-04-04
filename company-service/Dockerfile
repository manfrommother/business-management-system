# Базовый образ Python
FROM python:3.10-slim

# Установка рабочей директории
WORKDIR /app

# Копирование файла зависимостей
COPY requirements.txt requirements.txt

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода приложения
COPY ./app /app

# Команда для запуска приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 