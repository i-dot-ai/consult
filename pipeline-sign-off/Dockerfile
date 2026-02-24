FROM public.ecr.aws/docker/library/python:3.11-slim-bullseye

# Create non-root user for security
RUN groupadd -g 1001 appgroup && \
    useradd -r -u 1001 -g appgroup -m -s /bin/bash appuser

WORKDIR /app

COPY pipeline-sign-off/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline-sign-off/find_themes_script.py .

# Change ownership of application directory
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Verify running as non-root and then execute script
ENTRYPOINT ["sh", "-c", "id && [ $(id -u) -ne 0 ] && echo 'Running as non-root user' || (echo 'ERROR: Running as root!' && exit 1); python find_themes_script.py \"$@\"", "--"]
