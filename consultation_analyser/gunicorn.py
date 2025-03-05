from django.conf import settings


workers = settings.WORKERS
bind = "0.0.0.0:8000"
accesslog = "-"
errorlog = "-"
timeout = settings.TIMEOUT
