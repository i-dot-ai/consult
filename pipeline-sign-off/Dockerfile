FROM python:3.11-slim-bullseye

WORKDIR /app

COPY pipeline-sign-off/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline-sign-off/sign_off_script.py .

ENTRYPOINT ["python", "sign_off_script.py"]
