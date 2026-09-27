FROM python:3.12-alpine

RUN pip install --no-cache-dir flask

COPY app /app
WORKDIR /app

EXPOSE 8099

CMD ["python3", "main.py"]
