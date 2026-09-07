#!/bin/sh

# Collect static files (skip in test environment - no static serving needed)
if [ "$(echo "$ENVIRONMENT" | tr '[:upper:]' '[:lower:]')" != "test" ]; then
  venv/bin/django-admin collectstatic --noinput
fi

venv/bin/django-admin prepare_environment
venv/bin/django-admin populate_history --auto --batchsize 1000

exec venv/bin/gunicorn -c ./gunicorn_config.py backend.wsgi
