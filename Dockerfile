# Production image: Python + Gunicorn, static files served by WhiteNoise.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN useradd --create-home --uid 1000 appuser

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# collectstatic needs settings to load; these dummy values are build-only and
# never used at runtime (real values come from the environment).
RUN SECRET_KEY=build-only DB_NAME=build DB_USER=build DB_PASSWORD=build \
        python manage.py collectstatic --noinput \
    && mkdir -p /app/media \
    && chown appuser:appuser /app/media \
    && chmod +x /app/docker-entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--config", "gunicorn.conf.py"]
