FROM python:3.11-slim-bullseye

WORKDIR /app

COPY pipeline-mapping/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline-mapping/mapping_script.py .

ENTRYPOINT ["python", "mapping_script.py"]
