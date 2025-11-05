FROM public.ecr.aws/docker/library/python:3.11-slim-bullseye

WORKDIR /app

COPY pipeline-mapping/requirements.txt .

COPY pipeline-mapping/mapping_script.py .

ENTRYPOINT ["python", "mapping_script.py"]
