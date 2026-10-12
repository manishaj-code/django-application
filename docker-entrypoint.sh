#!/bin/sh
# Container start-up: apply migrations, then start the given command.
# Set RUN_MIGRATIONS=0 when running several replicas and migrating separately.
set -e

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    python manage.py migrate --noinput
    python manage.py createcachetable
fi

# Optional first admin account for hosts without shell access (e.g. Render
# free plan). Needs DJANGO_SUPERUSER_USERNAME, _EMAIL and _PASSWORD; does
# nothing if that username already exists.
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    python manage.py createsuperuser --noinput 2>/dev/null \
        && echo "Created superuser ${DJANGO_SUPERUSER_USERNAME}." \
        || echo "Superuser ${DJANGO_SUPERUSER_USERNAME} not created (usually: it already exists)."
fi

exec "$@"
