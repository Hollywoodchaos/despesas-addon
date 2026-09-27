ARG BUILD_FROM
FROM $BUILD_FROM

# Python + Flask (o servidor web do addon)
RUN apk add --no-cache python3 py3-pip

COPY app/requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /app/requirements.txt

COPY app /app

# Script de servico do s6-overlay - e ele que arranca o Flask, nunca um
# CMD direto (a base image ja usa s6-overlay como PID 1; um CMD proprio
# quebra essa cadeia de arranque com "s6-overlay-suexec: can only run as pid 1").
COPY rootfs /
RUN chmod a+x /etc/services.d/despesas/run

EXPOSE 8099
