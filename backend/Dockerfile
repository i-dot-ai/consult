# uv
FROM python:3.12.3-slim AS uv-packages

RUN apt-get update && apt-get install --yes build-essential > /dev/null

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set up workspace at /src so the layout matches the repo: pyproject + uv.lock at root,
# with backend/ and themefinder/ as workspace members.
WORKDIR /src

COPY ./pyproject.toml ./uv.lock ./
COPY ./themefinder/pyproject.toml ./themefinder/pyproject.toml
COPY ./themefinder/src/ ./themefinder/src/
COPY ./backend/pyproject.toml ./backend/pyproject.toml

WORKDIR /src/backend

# Configure uv to create venv in 'venv' directory instead of '.venv'
ENV UV_PROJECT_ENVIRONMENT=venv

# Install dependencies (workspace-aware) - creates /src/backend/venv with an editable
# install pointing at /src/themefinder/src
RUN uv sync --frozen --no-install-project


# app
FROM python:3.12.3-slim

RUN apt-get update && apt-get install --yes libpq-dev > /dev/null

# Add non-root user and group
RUN groupadd --system nonroot && useradd --system --gid nonroot nonroot

WORKDIR /src

# uv installs the themefinder workspace member as editable; the venv contains a .pth
# pointing at /src/themefinder/src, so that path must exist at runtime too.
COPY --chown=nonroot:nonroot ./themefinder/pyproject.toml ./themefinder/pyproject.toml
COPY --chown=nonroot:nonroot ./themefinder/src/ ./themefinder/src/

COPY --chown=nonroot:nonroot ./backend ./backend

COPY --from=uv-packages --chown=nonroot:nonroot /src/backend/venv ./backend/venv

ENV DJANGO_SETTINGS_MODULE='backend.settings.production'
ENV PYTHONPATH="${PYTHONPATH}:/src/"

EXPOSE 8000

WORKDIR /src/backend

# Run under context of "nonroot" user
USER nonroot

CMD ["./start.sh"]
