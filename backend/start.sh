#!/bin/sh

/usr/local/venv/bin/django-admin migrate
/usr/local/venv/bin/django-admin collectstatic --noinput
/usr/local/venv/bin/django-admin createadminusers
/usr/local/venv/bin/django-admin populate_history --auto --batchsize 1000

exec /usr/local/venv/bin/gunicorn -c ./gunicorn.py backend.wsgi
