FROM python:3.12-slim

# Create a non-root user to run the application
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy project metadata and source code
COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir .

# Give the appuser ownership so it can write payload JSON files
RUN chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["unifi-led"]
CMD ["--help"]
