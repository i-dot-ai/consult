# poetry
FROM python:3.12.3-slim AS poetry-packages

RUN apt-get update && apt-get install --yes build-essential > /dev/null

RUN pip install poetry poetry-plugin-bundle

WORKDIR /src

COPY ./backend/pyproject.toml .
COPY ./backend/poetry.lock .

# do this so that poetry bundle can run without the project - can't pass --no-root to bundle
RUN touch README.md

RUN poetry bundle venv ./venv


# app
FROM python:3.12.3-slim

RUN apt-get update && apt-get install --yes libpq-dev > /dev/null

WORKDIR /src

COPY ./backend ./backend

COPY --from=poetry-packages /src/venv ./backend/venv

ENV DJANGO_SETTINGS_MODULE='backend.settings.production'
ENV PYTHONPATH "${PYTHONPATH}:/src/"

EXPOSE 8000

WORKDIR /src/backend

CMD ["./start.sh"]
