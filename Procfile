web: poetry run gunicorn --reload --workers=1 -c consultation_analyser/gunicorn.py consultation_analyser.wsgi
worker: OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES poetry run python manage.py rqworker default --worker-class 'rq.worker.SimpleWorker' # ENV var permits multithreading on MacOS
worker2: OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES poetry run python manage.py rqworker default --worker-class 'rq.worker.SimpleWorker' # ENV var permits multithreading on MacOS
