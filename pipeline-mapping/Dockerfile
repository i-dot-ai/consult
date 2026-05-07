# uv-packages stage: build the venv
FROM public.ecr.aws/docker/library/python:3.12-slim AS uv-packages

RUN apt-get update && apt-get install --yes build-essential > /dev/null

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /src
COPY pyproject.toml uv.lock .python-version ./
COPY themefinder/pyproject.toml ./themefinder/
COPY themefinder/src/ ./themefinder/src/
COPY backend/pyproject.toml ./backend/
COPY pipeline-sign-off/pyproject.toml ./pipeline-sign-off/
COPY pipeline-mapping/pyproject.toml ./pipeline-mapping/
COPY pipeline-mapping/assign_themes_script.py ./pipeline-mapping/

WORKDIR /src/pipeline-mapping
ENV UV_PROJECT_ENVIRONMENT=/src/pipeline-mapping/venv
RUN uv sync --frozen --package pipeline-mapping


# runtime stage
FROM public.ecr.aws/docker/library/python:3.12-slim

RUN groupadd --system nonroot && useradd --system --gid nonroot nonroot

WORKDIR /src
COPY ./pipeline-mapping ./pipeline-mapping
COPY ./themefinder/pyproject.toml ./themefinder/
COPY ./themefinder/src ./themefinder/src
COPY --from=uv-packages /src/pipeline-mapping/venv ./pipeline-mapping/venv

RUN chown -R nonroot:nonroot /src

WORKDIR /src/pipeline-mapping
USER nonroot
ENV PATH="/src/pipeline-mapping/venv/bin:$PATH"
ENTRYPOINT ["python", "assign_themes_script.py"]
