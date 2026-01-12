FROM public.ecr.aws/docker/library/python:3.11-slim-bullseye

WORKDIR /app

COPY pipeline-mapping/requirements.txt .

COPY pipeline-mapping/assign_themes_script.py .

ENTRYPOINT ["python", "assign_themes_script.py"]
