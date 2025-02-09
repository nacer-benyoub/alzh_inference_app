FROM python:3.10.12-slim

RUN apt-get update

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "/app/app.py"]