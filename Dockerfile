FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    portaudio19-dev \
    python3-pyaudio \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    festival \
    festvox-kallpc16k \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs pids orchestrator/faiss

# Expose ports
EXPOSE 8000 8001 8002 8003 8004 8005 8011 8501

# Set environment variables
ENV PYTHONPATH=/app
ENV MISTRAL_API_KEY=NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal

# Default command
CMD ["python", "main.py"] 