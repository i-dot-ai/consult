#!/bin/sh

venv/bin/django-admin migrate
venv/bin/django-admin createadminusers

exec venv/bin/gunicorn -c ./consultation_analyser/gunicorn.py consultation_analyser.wsgi
