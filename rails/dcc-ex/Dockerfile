FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    paho-mqtt \
    pyserial-asyncio

COPY bridge.py /app_backup/bridge.py
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Use entrypoint to handle volume initialization
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
