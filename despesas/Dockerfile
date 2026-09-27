ARG BUILD_FROM
FROM $BUILD_FROM

# Python + Flask (o servidor web do addon)
RUN apk add --no-cache python3 py3-pip

COPY app/requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /app/requirements.txt

COPY app /app
WORKDIR /app

EXPOSE 8099

CMD ["python3", "main.py"]
