FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for media processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    wget \
    git \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/output

# Set environment variables
ENV PYTHONPATH=/app
ENV USE_MOCK=false

# Expose port
EXPOSE 8001

# Run the content agent
CMD ["python", "main.py"]
