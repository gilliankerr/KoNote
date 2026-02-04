FROM python:3.12-slim

# Security: run as non-root user
RUN groupadd -r konote && useradd -r -g konote -m konote

WORKDIR /app

# WeasyPrint system dependencies (PDF export) + gettext (for translation compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    shared-mime-info \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build-time commands use konote.settings.build (no env vars needed)
# Validate translations first - gives clear error messages if there are problems
RUN python scripts/validate_translations.py
RUN python manage.py compilemessages --settings=konote.settings.build
RUN python manage.py collectstatic --noinput --settings=konote.settings.build

# Make entrypoint executable and create fontconfig cache dir for non-root user
RUN chmod +x /app/entrypoint.sh && mkdir -p /home/konote/.cache/fontconfig && chown -R konote:konote /home/konote

# Switch to non-root user
USER konote

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
