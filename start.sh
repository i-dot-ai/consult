#!/bin/sh

venv/bin/django-admin migrate
exec venv/bin/gunicorn -c ./consultation_analyser/gunicorn.py consultation_analyser.wsgi
