FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: show help. Override CMD to run led on/off or fetch-config.
# Examples:
#   docker run --env-file .env unifi-led-api led on
#   docker run --env-file .env unifi-led-api led off
#   docker run --env-file .env unifi-led-api fetch-config
ENTRYPOINT ["python", "start.py"]
CMD ["--help"]
