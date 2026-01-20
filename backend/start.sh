#!/bin/sh

venv/bin/python manage.py migrate
venv/bin/python manage.py createadminusers
venv/bin/python manage.py populate_history --auto --batchsize 1000

echo "Starting gunicorn..."
echo "Python path: $PYTHONPATH"
echo "Working directory: $(pwd)"
echo "Testing WSGI import..."
venv/bin/python -c "import backend.wsgi; print('WSGI import successful')"

echo "Starting gunicorn with verbose logging..."
exec venv/bin/python -m gunicorn -c ./gunicorn.py backend.wsgi --log-level debug
