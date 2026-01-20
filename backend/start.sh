#!/bin/sh

../venv/bin/python manage.py migrate
../venv/bin/python manage.py collectstatic --noinput

# Skip createadminusers and populate_history in production if they fail
../venv/bin/python manage.py createadminusers || true
../venv/bin/python manage.py populate_history --auto --batchsize 1000 || true

exec ../venv/bin/python -m gunicorn -c ./gunicorn.py backend.wsgi
