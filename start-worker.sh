#!/bin/sh

exec venv/bin/python3.12 manage.py db_worker --queue-name default
