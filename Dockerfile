FROM python:3.12-slim

# Create a non-root user to run the application
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy project metadata first for better layer caching
COPY pyproject.toml README.md ./
COPY *.py ./

RUN pip install --no-cache-dir .

# Give the appuser ownership so it can write payload JSON files
RUN chown -R appuser:appuser /app

USER appuser

# Default: show help. Override CMD to run led on/off or fetch-config.
# Examples:
#   docker run --env-file .env unifi-led-api led on
#   docker run --env-file .env unifi-led-api led off
#   docker run --env-file .env unifi-led-api status
#   docker run --env-file .env unifi-led-api fetch-config
ENTRYPOINT ["python", "start.py"]
CMD ["--help"]
