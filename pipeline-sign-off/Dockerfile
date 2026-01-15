FROM public.ecr.aws/docker/library/python:3.11-slim-bullseye

WORKDIR /app

COPY pipeline-sign-off/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline-sign-off/find_themes_script.py .

ENTRYPOINT ["python", "find_themes_script.py"]
