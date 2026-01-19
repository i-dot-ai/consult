import os

workers = os.environ.get("GUNICORN_WORKERS")
bind = "0.0.0.0:8000"
accesslog = "-"
errorlog = "-"
timeout = os.environ.get("GUNICORN_TIMEOUT")
