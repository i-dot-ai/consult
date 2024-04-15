#!/bin/sh

poetry run django-admin migrate
poetry run django-admin compress --force --engine jinja2
exec poetry run gunicorn -c ./consultation_analyser/gunicorn.py consultation_analyser.wsgi
