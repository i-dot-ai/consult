FROM public.ecr.aws/docker/library/python:3.12-slim AS uv-packages

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /uvx /bin/

# Only the manifests required by the target package are copied; uv tolerates missing
# non-target workspace members.
WORKDIR /src
COPY pyproject.toml uv.lock .python-version ./
COPY pipeline-mapping/pyproject.toml ./pipeline-mapping/
COPY themefinder/pyproject.toml ./themefinder/
COPY themefinder/src/ ./themefinder/src/
COPY pipeline-common/pyproject.toml ./pipeline-common/
COPY pipeline-common/src/ ./pipeline-common/src/

WORKDIR /src/pipeline-mapping
ENV UV_PROJECT_ENVIRONMENT=/src/pipeline-mapping/venv
RUN uv sync --frozen --package pipeline-mapping


FROM public.ecr.aws/docker/library/python:3.12-slim

RUN groupadd --system nonroot && useradd --system --gid nonroot nonroot

WORKDIR /src
# themefinder src must be present at runtime — venv has an editable .pth pointing at it.
COPY --chown=nonroot:nonroot themefinder/src ./themefinder/src
# pipeline-common src must be present at runtime — venv has an editable .pth pointing at it.
COPY --chown=nonroot:nonroot pipeline-common/src ./pipeline-common/src
COPY --chown=nonroot:nonroot pipeline-mapping/assign_themes_script.py ./pipeline-mapping/
COPY --chown=nonroot:nonroot --from=uv-packages /src/pipeline-mapping/venv ./pipeline-mapping/venv

WORKDIR /src/pipeline-mapping
USER nonroot
ENV PATH="/src/pipeline-mapping/venv/bin:$PATH"
ENTRYPOINT ["python", "assign_themes_script.py"]
