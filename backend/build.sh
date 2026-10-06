#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Collecting static assets..."
python manage.py collectstatic --no-input --settings=config.settings.production

echo "==> Running database migrations..."
python manage.py migrate --no-input --settings=config.settings.production

echo "==> Build completed successfully!"
