FROM python:3.12-slim

# Security: run as non-root user
RUN groupadd -r konote && useradd -r -g konote konote

WORKDIR /app

# WeasyPrint system dependencies (PDF export)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files (errors shown for debugging)
RUN FIELD_ENCRYPTION_KEY=dummy-build-key SECRET_KEY=dummy-build-key ALLOWED_HOSTS=* python manage.py collectstatic --noinput --settings=konote.settings.production

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER konote

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
