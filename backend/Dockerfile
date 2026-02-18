# uv
FROM python:3.12.3-slim AS uv-packages

RUN apt-get update && apt-get install --yes build-essential > /dev/null

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ./backend/pyproject.toml ./backend/uv.lock ./

# Create venv at the final destination path to avoid shebang issues
RUN uv venv /src/backend/venv

ENV VIRTUAL_ENV=/src/backend/venv
ENV PATH="/src/backend/venv/bin:$PATH"

RUN uv sync --frozen --no-dev --no-install-project


# app
FROM python:3.12.3-slim

RUN apt-get update && apt-get install --yes libpq-dev > /dev/null

WORKDIR /src

COPY ./backend ./backend

COPY --from=uv-packages /src/backend/venv ./backend/venv

ENV DJANGO_SETTINGS_MODULE='backend.settings.production'
ENV PYTHONPATH "${PYTHONPATH}:/src/"

EXPOSE 8000

WORKDIR /src/backend

CMD ["./start.sh"]
