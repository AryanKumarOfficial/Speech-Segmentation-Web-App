# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    APP_DIR=/app

WORKDIR ${APP_DIR}

# Install ffmpeg + minimal build deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg gcc && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . ${APP_DIR}

# Ensure output dir exists (your app writes into OUTPUT_ROOT)
RUN mkdir -p /app/output

EXPOSE ${PORT}

# Start via the root entrypoint which uses the PORT env var
CMD ["sh", "-c", "python main.py"]
