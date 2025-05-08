#!/bin/sh

echo "Waiting for database..."
python manage.py wait_for_db

echo "Applying migrations..."
python manage.py migrate

echo "Starting Celery worker..."
celery -A api_config worker --loglevel=INFO --pool=solo &

echo "Starting Django server..."
exec python manage.py runserver 0.0.0.0:8000
