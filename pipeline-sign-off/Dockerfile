FROM public.ecr.aws/docker/library/python:3.12-slim AS uv-packages

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /uvx /bin/

# Only the manifests required by the target package are copied; uv tolerates missing
# non-target workspace members.
WORKDIR /src
COPY pyproject.toml uv.lock .python-version ./
COPY pipeline-sign-off/pyproject.toml ./pipeline-sign-off/
COPY themefinder/pyproject.toml ./themefinder/
COPY themefinder/src/ ./themefinder/src/
COPY pipeline-common/pyproject.toml ./pipeline-common/
COPY pipeline-common/src/ ./pipeline-common/src/

WORKDIR /src/pipeline-sign-off
ENV UV_PROJECT_ENVIRONMENT=/src/pipeline-sign-off/venv
RUN uv sync --frozen --package pipeline-sign-off


FROM public.ecr.aws/docker/library/python:3.12-slim

RUN groupadd --system nonroot && useradd --system --gid nonroot nonroot

WORKDIR /src
# themefinder src must be present at runtime — venv has an editable .pth pointing at it.
COPY --chown=nonroot:nonroot themefinder/src ./themefinder/src
# pipeline-common src must be present at runtime — venv has an editable .pth pointing at it.
COPY --chown=nonroot:nonroot pipeline-common/src ./pipeline-common/src
COPY --chown=nonroot:nonroot pipeline-sign-off/find_themes_script.py ./pipeline-sign-off/
COPY --chown=nonroot:nonroot --from=uv-packages /src/pipeline-sign-off/venv ./pipeline-sign-off/venv

WORKDIR /src/pipeline-sign-off
USER nonroot
ENV PATH="/src/pipeline-sign-off/venv/bin:$PATH"
ENTRYPOINT ["python", "find_themes_script.py"]
