# uv-packages stage: build the venv
FROM public.ecr.aws/docker/library/python:3.12-slim AS uv-packages

RUN apt-get update && apt-get install --yes build-essential > /dev/null

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /src
COPY pyproject.toml uv.lock .python-version ./
COPY themefinder/pyproject.toml ./themefinder/
COPY themefinder/src/ ./themefinder/src/
COPY backend/pyproject.toml ./backend/
COPY pipeline-mapping/pyproject.toml ./pipeline-mapping/
COPY pipeline-sign-off/pyproject.toml ./pipeline-sign-off/
COPY pipeline-sign-off/find_themes_script.py ./pipeline-sign-off/

WORKDIR /src/pipeline-sign-off
ENV UV_PROJECT_ENVIRONMENT=/src/pipeline-sign-off/venv
RUN uv sync --frozen --package pipeline-sign-off


# runtime stage
FROM public.ecr.aws/docker/library/python:3.12-slim

RUN groupadd --system nonroot && useradd --system --gid nonroot nonroot

WORKDIR /src
COPY ./pipeline-sign-off ./pipeline-sign-off
COPY ./themefinder/pyproject.toml ./themefinder/
COPY ./themefinder/src ./themefinder/src
COPY --from=uv-packages /src/pipeline-sign-off/venv ./pipeline-sign-off/venv

RUN chown -R nonroot:nonroot /src

WORKDIR /src/pipeline-sign-off
USER nonroot
ENV PATH="/src/pipeline-sign-off/venv/bin:$PATH"
ENTRYPOINT ["python", "find_themes_script.py"]
