FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=600

# Install system dependencies including PostgreSQL development headers
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     libpq-dev     && apt-get clean     && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies individually to avoid timeout issues
RUN pip install --no-cache-dir --upgrade pip &&     pip install --no-cache-dir fastapi==0.115.12 &&     pip install --no-cache-dir uvicorn==0.34.0 &&     pip install --no-cache-dir psycopg2-binary==2.9.10 &&     pip install --no-cache-dir python-dotenv==1.1.0 &&     pip install --no-cache-dir loguru==0.7.3 &&     pip install --no-cache-dir python-magic==0.4.27 &&     pip install --no-cache-dir numpy==2.2.4 &&     pip install --no-cache-dir pandas==2.2.3

# Copy application code
COPY . .

# Create a non-root user
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app
USER appuser

# Add health check endpoint
RUN if ! grep -q "def health" main.py; then     echo -e "\n@app.get('/health')\ndef health():\n    return {'status': 'healthy'}" >> main.py; fi

# Expose API port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
