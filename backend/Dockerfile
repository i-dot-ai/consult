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
RUN uv sync --frozen --no-dev --no-install-project


# app
FROM python:3.12.3-slim

RUN apt-get update && apt-get install --yes libpq-dev > /dev/null

WORKDIR /src

COPY ./backend ./backend

COPY --from=uv-packages /src/backend/venv ./backend/venv

ENV DJANGO_SETTINGS_MODULE='backend.settings.production'
ENV PYTHONPATH="${PYTHONPATH}:/src/"

EXPOSE 8000

WORKDIR /src/backend

CMD ["./start.sh"]
