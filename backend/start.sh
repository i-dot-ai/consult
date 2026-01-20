#!/bin/sh

venv/bin/django-admin migrate
venv/bin/django-admin createadminusers
venv/bin/django-admin populate_history --auto --batchsize 1000

echo "Starting gunicorn..."
echo "Python path: $PYTHONPATH"
echo "Working directory: $(pwd)"
echo "Testing WSGI import..."
venv/bin/python -c "import backend.wsgi; print('WSGI import successful')"

echo "Starting gunicorn with verbose logging..."
exec venv/bin/gunicorn -c ./gunicorn_config.py backend.wsgi --log-level debug
