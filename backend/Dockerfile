# uv
FROM python:3.12.3-slim AS uv-packages

RUN apt-get update && apt-get install --yes build-essential > /dev/null

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /src

# Copy workspace root config and lockfile
COPY pyproject.toml uv.lock ./

# Copy themefinder package (workspace member)
COPY themefinder/pyproject.toml ./themefinder/pyproject.toml
COPY themefinder/src/ ./themefinder/src/

# Copy backend package config
COPY backend/pyproject.toml ./backend/pyproject.toml

# Install dependencies (resolves themefinder from workspace)
WORKDIR /src/backend
ENV UV_PROJECT_ENVIRONMENT=/src/backend/venv
RUN uv sync --frozen --no-install-project


# app
FROM python:3.12.3-slim

RUN apt-get update && apt-get install --yes libpq-dev > /dev/null

# Add non-root user and group
RUN groupadd --system nonroot && useradd --system --gid nonroot nonroot

WORKDIR /src

COPY ./backend ./backend

COPY --from=uv-packages /src/backend/venv ./backend/venv

# Change ownership of application directory
RUN chown -R nonroot:nonroot /src

ENV DJANGO_SETTINGS_MODULE='backend.settings.production'
ENV PYTHONPATH="${PYTHONPATH}:/src/"

EXPOSE 8000

WORKDIR /src/backend

# Run under context of "nonroot" user
USER nonroot

CMD ["./start.sh"]
