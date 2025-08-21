FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir beautifulsoup4 nltk openai aiohttp aiofiles

# Copy all Python scripts and configuration files
COPY *.py ./
COPY *.json ./
COPY *.md ./
COPY regenerate_translations/ ./regenerate_translations/
# COPY regenerate_tts_es/ ./regenerate_tts_es/

# Set environment variable to indicate Docker environment
ENV DOCKER_ENV=true

# Default command shows help
CMD ["python", "standardize_all.py", "--help"]
