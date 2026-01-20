#!/bin/sh

venv/bin/python manage.py migrate
venv/bin/python manage.py createadminusers
venv/bin/python manage.py populate_history --auto --batchsize 1000

exec venv/bin/python -m gunicorn -c ./gunicorn.py backend.wsgi
