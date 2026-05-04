FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Install Render CLI
ARG RENDER_CLI_VERSION=v2.16.0
RUN curl -L "https://github.com/render-oss/cli/releases/download/${RENDER_CLI_VERSION}/render-linux-x86_64" -o /usr/local/bin/render \
    && chmod +x /usr/local/bin/render

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app
# Note: .env should ideally be passed via environment variables in production (Render)

ENV PYTHONPATH=/app
ENV PORT=10000

EXPOSE 10000

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:10000"]
