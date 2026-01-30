FROM public.ecr.aws/docker/library/python:3.11-slim-bullseye

WORKDIR /app

COPY pipeline-mapping/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline-mapping/assign_themes_script.py .

ENTRYPOINT ["python", "assign_themes_script.py"]
