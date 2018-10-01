FROM python:3.6

WORKDIR /app
ADD . /app

RUN pip install -r ./backend/requirements.txt

CMD ["python", "bot.py"]
