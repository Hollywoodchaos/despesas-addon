FROM python:3.12-alpine

RUN pip install --no-cache-dir flask==3.0.3

COPY app /app
WORKDIR /app

ENV DESPESAS_PORT=8099
EXPOSE 8099

CMD ["python3", "main.py"]
