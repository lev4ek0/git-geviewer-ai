# получаем image для нашего питона
FROM python:3.11

# задаём переменные окружения, чтобы
# предотвратить ряд событий, а именно:
# создания .pyc файлов и использования
# питоном буффера для stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y && apt-get upgrade -y

RUN apt-get install libpq-dev
RUN apt-get install -y poppler-utils
RUN apt-get install -y wkhtmltopdf

# устанавливаем рабочую директорию
WORKDIR /bot

# ставим python зависимости
RUN pip install --upgrade pip
COPY requirements .
RUN pip install -r production.txt

# копируем проект
COPY . .
