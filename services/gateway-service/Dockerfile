FROM python:3.12-slim

# Create a dedicated non-root user
RUN useradd --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Run as non-root
USER appuser

EXPOSE 5000

# Production WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]