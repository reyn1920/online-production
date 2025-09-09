FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    wkhtmltopdf \
    pandoc \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-extra \
    imagemagick \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/output /app/templates

# Set environment variables
ENV PYTHONPATH=/app
ENV USE_MOCK=false
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8003

# Run the monetization bundle
CMD ["python", "main.py"]