# backend_v2/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend_v2/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend_v2 /app/backend_v2
COPY .env /app/.env

ENV PYTHONPATH=/app
ENV PORT=8001

EXPOSE 8001

CMD ["python", "backend_v2/main.py"]
