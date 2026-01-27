import os

workers = int(os.environ.get("GUNICORN_WORKERS", "1"))
bind = "0.0.0.0:8000"
accesslog = "-"
errorlog = "-"
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "30"))
