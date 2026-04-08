FROM public.ecr.aws/docker/library/python:3.11-slim-bullseye

WORKDIR /app

COPY themefinder/ ./themefinder/
RUN pip install --no-cache-dir ./themefinder

COPY pipeline-sign-off/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline-sign-off/find_themes_script.py .

# Add non-root user and group
RUN groupadd --system nonroot && useradd --system --gid nonroot nonroot

# Change ownership of application directory
RUN chown -R nonroot:nonroot /app

# Run under context of "nonroot" user
USER nonroot

ENTRYPOINT ["python", "find_themes_script.py"]
