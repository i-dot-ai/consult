# npm
# use the same base image as the others for efficiency
FROM python:3.12-slim AS npm-packages

RUN apt-get update && apt-get install --yes nodejs npm > /dev/null

WORKDIR /src

COPY package.json .
RUN npm install

# app
FROM python:3.12-slim

RUN apt-get update && apt-get install --yes libpq-dev build-essential > /dev/null

WORKDIR /usr/src/app

COPY --from=npm-packages /src/node_modules ./node_modules

COPY pyproject.toml .
COPY poetry.lock .
COPY README.md .

RUN pip install poetry
RUN poetry install

COPY . .

ENV DJANGO_SETTINGS_MODULE='consultation_analyser.settings.production'
ENV PYTHONPATH "${PYTHONPATH}:/."

EXPOSE 8000

CMD ["./start.sh"]
