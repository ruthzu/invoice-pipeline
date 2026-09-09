FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

# Run the application without root privileges.
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/storage \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
