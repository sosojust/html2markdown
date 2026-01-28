FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for building some python packages)
# RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
