#!/bin/sh

venv/bin/django-admin migrate
venv/bin/django-admin collectstatic --noinput
venv/bin/django-admin createadminusers
venv/bin/django-admin populate_history --auto --batchsize 1000

exec venv/bin/gunicorn -c ./gunicorn.py ./wsgi
