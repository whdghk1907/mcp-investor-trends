FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY tests/ tests/
COPY pytest.ini .
COPY pyproject.toml .

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=postgresql://postgres:password@postgres:5432/investor_trends
ENV REDIS_URL=redis://redis:6379/0

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "src.main"]