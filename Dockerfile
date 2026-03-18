FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts and config
COPY scripts/ scripts/
COPY config/ config/

# Default: run the news fetcher
CMD ["python", "scripts/fetch_news.py"]
