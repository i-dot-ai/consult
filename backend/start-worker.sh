#!/bin/sh

exec venv/bin/python3.12 manage.py rqworker default
