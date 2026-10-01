#!/bin/sh
set -e

if [ -n "$REDIS_HOST" ]; then
  echo "Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT:-6379}..."
  while ! nc -z "${REDIS_HOST}" "${REDIS_PORT:-6379}"; do
    sleep 0.5
  done
  echo "Redis is online and accessible."
fi

exec "$@"
