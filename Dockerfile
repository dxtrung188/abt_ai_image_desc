# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Set workdir
WORKDIR /app

# Install system dependencies (if any needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY main.py ./
COPY utils.py ./
COPY logging_config.yaml ./
COPY templates ./templates
COPY static ./static
COPY images ./images

# Expose port
EXPOSE 8000

# Entrypoint
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-config", "logging_config.yaml"]

# Note: .env file should be provided via docker-compose or bind mount for secrets. 