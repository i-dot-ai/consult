# uv
FROM python:3.12.3-slim AS uv-packages

RUN apt-get update && apt-get install --yes build-essential > /dev/null

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set up the project directory structure
WORKDIR /src/backend

COPY ./backend/pyproject.toml ./backend/uv.lock ./

# Configure uv to create venv in 'venv' directory instead of '.venv'
ENV UV_PROJECT_ENVIRONMENT=venv

# Install dependencies - this will create venv directory
RUN uv sync --frozen --no-install-project


# app
FROM python:3.12.3-slim

RUN apt-get update && apt-get install --yes libpq-dev > /dev/null

# Create non-root user for security
RUN groupadd -g 1001 appgroup && \
    useradd -r -u 1001 -g appgroup -m -s /bin/bash appuser

WORKDIR /src

COPY ./backend ./backend

COPY --from=uv-packages /src/backend/venv ./backend/venv

# Change ownership of application directory
RUN chown -R appuser:appgroup /src

# Switch to non-root user
USER appuser

ENV DJANGO_SETTINGS_MODULE='backend.settings.production'
ENV PYTHONPATH="${PYTHONPATH}:/src/"

EXPOSE 8000

WORKDIR /src/backend

# Verify running as non-root before starting
CMD ["sh", "-c", "id && [ $(id -u) -ne 0 ] && echo 'Running as non-root user' || (echo 'ERROR: Running as root!' && exit 1); ./start.sh"]
