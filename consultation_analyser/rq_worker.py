# rq_worker.py
import os
import django
from django.conf import settings
from rq import Worker, Queue, Connection
from redis import Redis
import multiprocessing
import time
import logging

logger = logging.getLogger("Worker")

# Set 'spawn' method to avoid fork() issues on macOS
multiprocessing.set_start_method('spawn')

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "consultation_analyser.settings.local")
django.setup()

def worker_process(queue_name):
    # Connect to Redis server
    redis_host = os.getenv('REDIS_HOST')
    redis_port = os.getenv('REDIS_PORT')
    redis_url = f'redis://{redis_host}:{redis_port}'
    conn = Redis.from_url(redis_url)

    # Create RQ worker
    with Connection(conn):
        worker = Worker([Queue(queue_name)])
        while True:
            try:
                worker.work(burst=True)
            except Exception as e:
                print(f"Worker error: {e}")
            time.sleep(5)  # Sleep for a while before retrying

if __name__ == '__main__':
    # Start worker process
    worker_process('default')