#!/bin/sh

# Collect static files
venv/bin/django-admin collectstatic --noinput

# Fix migration names renamed in d5828a78 but not updated in dev DB
venv/bin/python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(
        \"UPDATE django_migrations SET name = %s WHERE app = %s AND name = %s\",
        ['0095_fileupload_remove_response_unique_question_response_and_more', 'consultations', '0094_fileupload_remove_response_unique_question_response_and_more']
    )
    cursor.execute(
        \"UPDATE django_migrations SET name = %s WHERE app = %s AND name = %s\",
        ['0096_question_status', 'consultations', '0095_question_status']
    )
    print(f'Migration name fix: {cursor.rowcount} rows updated')
" 2>/dev/null || true

venv/bin/django-admin migrate
venv/bin/django-admin createadminusers
venv/bin/django-admin populate_history --auto --batchsize 1000

exec venv/bin/gunicorn -c ./gunicorn_config.py backend.wsgi
