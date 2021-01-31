FROM python:3.9.1-alpine3.12

RUN apk update
RUN apk add bash
RUN apk add vim

WORKDIR /app

COPY requirements.txt .
COPY AFILinkerBot.py .
COPY smarmycomments.txt .

RUN pip install -r requirements.txt

CMD ["python", "./AFILinkerBot.py"]

