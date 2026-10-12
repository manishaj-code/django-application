#!/bin/sh
# Container start-up: apply migrations, then start the given command.
# Set RUN_MIGRATIONS=0 when running several replicas and migrating separately.
set -e

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    python manage.py migrate --noinput
    python manage.py createcachetable
fi

exec "$@"
