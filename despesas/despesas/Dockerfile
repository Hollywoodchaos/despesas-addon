ARG BUILD_FROM
FROM $BUILD_FROM

# Flask (o servidor web do addon) - imagem Python simples, sem
# sistema de arranque proprio (nada de s6-overlay), para evitar
# qualquer conflito com o processo de arranque do Supervisor.
RUN pip install --no-cache-dir flask

COPY app /app
WORKDIR /app

EXPOSE 8099

CMD ["python3", "main.py"]
