#!/usr/bin/bash

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  echo "Waiting for PostgreSQL to start..."
  sleep 10
done

echo "PostgreSQL started. Applying migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting uwsgi..."
uwsgi --strict --ini /opt/app/uwsgi.ini
