#!/bin/sh
set -e

echo "Waiting for PostgreSQL at ${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}..."
while ! nc -z "${POSTGRES_HOST:-postgres}" "${POSTGRES_PORT:-5432}"; do
  sleep 0.5
done
echo "PostgreSQL is online and accessible."

echo "Waiting for Redis at ${REDIS_HOST:-redis}:${REDIS_PORT:-6379}..."
while ! nc -z "${REDIS_HOST:-redis}" "${REDIS_PORT:-6379}"; do
  sleep 0.5
done
echo "Redis is online and accessible."

exec "$@"
