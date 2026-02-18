# uv
FROM python:3.12.3-slim AS uv-packages

RUN apt-get update && apt-get install --yes build-essential > /dev/null

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /src

COPY ./backend/pyproject.toml .
COPY ./backend/uv.lock .

RUN uv export --frozen --no-hashes --no-dev > requirements.txt
RUN uv pip install --python 3.12 --prefix=/src/venv -r requirements.txt


# app
FROM python:3.12.3-slim

RUN apt-get update && apt-get install --yes libpq-dev > /dev/null

WORKDIR /src

COPY ./backend ./backend

COPY --from=uv-packages /src/venv ./backend/venv

ENV DJANGO_SETTINGS_MODULE='backend.settings.production'
ENV PYTHONPATH "${PYTHONPATH}:/src/"

EXPOSE 8000

WORKDIR /src/backend

CMD ["./start.sh"]
