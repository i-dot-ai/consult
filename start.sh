#!/bin/sh

venv/bin/django-admin showmigrations
venv/bin/django-admin migrate
venv/bin/django-admin showmigrations
venv/bin/django-admin collectstatic --noinput
venv/bin/django-admin compress --force --engine jinja2
venv/bin/django-admin createadminusers

exec venv/bin/gunicorn -c ./consultation_analyser/gunicorn.py consultation_analyser.wsgi
