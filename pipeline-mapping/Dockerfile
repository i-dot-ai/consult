FROM public.ecr.aws/docker/library/python:3.12-slim AS uv-packages

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# All workspace member manifests are required for uv to resolve the workspace.
WORKDIR /src
COPY pyproject.toml uv.lock .python-version ./
COPY backend/pyproject.toml ./backend/
COPY pipeline-mapping/pyproject.toml ./pipeline-mapping/
COPY pipeline-sign-off/pyproject.toml ./pipeline-sign-off/
COPY themefinder/pyproject.toml ./themefinder/
COPY themefinder/src/ ./themefinder/src/

WORKDIR /src/pipeline-mapping
ENV UV_PROJECT_ENVIRONMENT=/src/pipeline-mapping/venv
RUN uv sync --frozen --package pipeline-mapping


FROM public.ecr.aws/docker/library/python:3.12-slim

RUN groupadd --system nonroot && useradd --system --gid nonroot nonroot

WORKDIR /src
# themefinder src must be present at runtime — venv has an editable .pth pointing at it.
COPY --chown=nonroot:nonroot themefinder/src ./themefinder/src
COPY --chown=nonroot:nonroot pipeline-mapping/assign_themes_script.py ./pipeline-mapping/
COPY --chown=nonroot:nonroot --from=uv-packages /src/pipeline-mapping/venv ./pipeline-mapping/venv

WORKDIR /src/pipeline-mapping
USER nonroot
ENV PATH="/src/pipeline-mapping/venv/bin:$PATH"
ENTRYPOINT ["python", "assign_themes_script.py"]
