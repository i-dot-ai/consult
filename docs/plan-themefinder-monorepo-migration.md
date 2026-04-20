# Plan: Move ThemeFinder into Consult as a Monorepo

## Context

Today, getting a themefinder change into consult requires: edit themefinder → bump version → merge → PyPI release → update 3 version pins in consult → rebuild Docker images → deploy. Two repos, two PRs, a PyPI release, and four Docker builds for what might be a one-line prompt change.

The two projects are tightly coupled — consult's pipeline scripts import themefinder internals (`themefinder.llm.OpenAILLM`, `themefinder.models.ThemeNode`, `themefinder.advanced_tasks.theme_clustering_agent`), and themefinder is effectively a private library with one real consumer. Moving themefinder into consult as a uv workspace member eliminates the release ceremony while keeping it publishable to PyPI for external users.

**After this migration, the dev loop becomes:** edit themefinder → it's immediately available in backend and pipelines → run tests → commit → single PR.

## Target Directory Structure

```
consult/
├── pyproject.toml              ← NEW: root workspace config (uv workspace only, not a package)
├── uv.lock                     ← NEW: single lockfile for the whole workspace
├── Makefile
├── docker-compose.yml
├── Procfile.dev
├── backend/
│   ├── pyproject.toml          ← MODIFIED: themefinder as workspace dependency
│   ├── Dockerfile              ← MODIFIED: copy themefinder source into build
│   └── ...
├── frontend/
├── themefinder/                ← NEW: moved from separate repo
│   ├── pyproject.toml          ← KEPT: unchanged (still publishable to PyPI)
│   ├── src/themefinder/
│   ├── tests/
│   ├── evals/
│   ├── docs/
│   ├── examples/
│   └── ...
├── pipeline-sign-off/
│   ├── Dockerfile              ← MODIFIED: copy + install local themefinder
│   ├── find_themes_script.py
│   └── requirements.txt        ← MODIFIED: remove themefinder line
├── pipeline-mapping/
│   ├── Dockerfile              ← MODIFIED: copy + install local themefinder
│   ├── assign_themes_script.py
│   └── requirements.txt        ← MODIFIED: remove themefinder line
└── .github/workflows/
    ├── themefinder-ci.yml      ← NEW: tests for themefinder
    ├── themefinder-eval.yml    ← NEW: LLM evals (moved from themefinder repo)
    ├── sync-themefinder.yml    ← NEW: auto-push to public repo
    ├── backend-ci.yml          ← MODIFIED: also trigger on themefinder/** changes
    └── ... (existing workflows)
```

## PR Structure

The migration is split into 3 PRs. Phases 1-3 must land together because the Docker build CI (`build-gh.yml`) runs on every push and builds all 4 images — if the workspace is set up but the Dockerfiles aren't updated, builds break.

| PR | Phases | What | Can merge independently? |
|---|---|---|---|
| **PR 1** | 1 + 2 + 3 | Core migration: copy themefinder, workspace config, Dockerfiles, Makefile | Yes (this is the big one) |
| **PR 2** | 4 | CI: add themefinder-ci.yml, themefinder-eval.yml, update backend-ci.yml triggers | Yes, after PR 1 |
| **PR 3** | 5 | Public repo sync: auto-push workflow, update public repo README | Yes, after PR 1 |

## Implementation Checklist

### PR 1: Core Migration

#### Phase 1: Copy and wire up the workspace

- [ ] Copy themefinder repo contents into `consult/themefinder/` (exclude `.git/`, `.github/`)
- [ ] Create root `consult/pyproject.toml` with uv workspace config:
  ```toml
  [tool.uv.workspace]
  members = ["backend", "themefinder"]
  ```
- [ ] Update `backend/pyproject.toml` — add workspace source for themefinder:
  ```toml
  [tool.uv.sources]
  themefinder = { workspace = true }
  ```
- [ ] Delete `backend/uv.lock` (workspace uses root-level lockfile)
- [ ] Run `uv lock` from repo root to generate new `consult/uv.lock`
- [ ] Verify: `uv sync` succeeds
- [ ] Verify: `uv run python -c "from themefinder.models import ThemeNode; print('ok')"` works
- [ ] Verify: `make test-backend` passes

#### Phase 2: Update pipeline Dockerfiles

- [ ] Remove `themefinder>=0.8.2` from `pipeline-sign-off/requirements.txt`
- [ ] Remove `themefinder>=0.8.2` from `pipeline-mapping/requirements.txt`
- [ ] Update `pipeline-sign-off/Dockerfile` to copy and install local themefinder:
  ```dockerfile
  COPY themefinder/ ./themefinder/
  RUN pip install --no-cache-dir ./themefinder
  ```
- [ ] Update `pipeline-mapping/Dockerfile` — same pattern
- [ ] Update `backend/Dockerfile` uv-packages stage to include workspace root + themefinder:
  ```dockerfile
  WORKDIR /src
  COPY pyproject.toml uv.lock ./
  COPY themefinder/pyproject.toml ./themefinder/pyproject.toml
  COPY themefinder/src/ ./themefinder/src/
  COPY backend/pyproject.toml ./backend/pyproject.toml
  WORKDIR /src/backend
  ENV UV_PROJECT_ENVIRONMENT=venv
  RUN uv sync --frozen --no-install-project
  ```
- [ ] Add to `.dockerignore`: `themefinder/evals/`, `themefinder/docs/`, `themefinder/tests/` (not needed in production images)
- [ ] Verify: `docker build -f pipeline-sign-off/Dockerfile .` succeeds
- [ ] Verify: `docker build -f pipeline-mapping/Dockerfile .` succeeds
- [ ] Verify: `docker build -f backend/Dockerfile .` succeeds

#### Phase 3: Update Makefile and local dev

- [ ] Update `make install` to run `uv sync` from workspace root (not `cd backend && uv sync`)
- [ ] Add `make test-themefinder` target: `cd themefinder && uv run pytest tests/ -v`
- [ ] Add `make test-all` target combining backend, frontend, and themefinder tests
- [ ] Add `make run-evals` target: `cd themefinder/evals && uv run python benchmark.py --quick`
- [ ] Verify: `make serve` starts successfully
- [ ] Verify: `make test-themefinder` passes
- [ ] Verify: full app works at localhost:3000

### PR 2: CI Migration

- [ ] Create `.github/workflows/themefinder-ci.yml` — runs themefinder tests on PR/push when `themefinder/**` changes (Python 3.10, 3.11, 3.12 matrix, 95% coverage gate)
- [ ] Create `.github/workflows/themefinder-eval.yml` — runs LLM evals on PR when `themefinder/**` changes, supports manual dispatch with dataset/eval_type inputs. Uses EC2 self-hosted runner via `i-dot-ai-core-github-actions`
- [ ] Update `.github/workflows/backend-ci.yml` — add `themefinder/**` to trigger paths, update `uv sync` to work with workspace
- [ ] Merge themefinder's pre-commit hooks (detect-secrets, nbstripout) into consult's root `.pre-commit-config.yaml`
- [ ] Copy required secrets to consult repo GitHub settings (eval environment):
  - `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_API_VERSION`
  - `LLM_GATEWAY_URL`, `CONSULT_EVAL_LITELLM_API_KEY`
  - `LOCAI_ENDPOINT`, `LOCAI_API_KEY`
  - `AUTO_EVAL_4_1_SWEDEN_DEPLOYMENT`
  - `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_BASE_URL`
  - `THEMEFINDER_S3_BUCKET_NAME`
  - `SLACK_WEBHOOK_URL`

### PR 3: Public Repo Sync

- [ ] Create `.github/workflows/sync-themefinder.yml` — auto-pushes `themefinder/` subtree to `i-dot-ai/themefinder` on merge to main:
  ```yaml
  name: Sync themefinder to public repo
  on:
    push:
      branches: [main]
      paths: ['themefinder/**']
  jobs:
    sync:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
          with:
            fetch-depth: 0
        - name: Push themefinder subtree to public repo
          run: |
            git remote add themefinder https://x-access-token:${{ secrets.THEMEFINDER_PUSH_TOKEN }}@github.com/i-dot-ai/themefinder.git
            git subtree split --prefix=themefinder -b themefinder-sync
            git push themefinder themefinder-sync:main --force
  ```
- [ ] Create `THEMEFINDER_PUSH_TOKEN` secret in consult repo (GitHub PAT with push access to `i-dot-ai/themefinder`)
- [ ] Update themefinder repo README to note that development happens in the consult monorepo
- [ ] Keep `deploy-pypi.yml` and `deploy-docs.yml` in the public themefinder repo (triggered by auto-sync)
- [ ] Verify: merge a test change to `themefinder/` and confirm it appears in the public repo

## Workflow Locations After Migration

| Workflow | Location | Trigger |
|---|---|---|
| ThemeFinder tests | consult repo | PR/push touching `themefinder/**` |
| ThemeFinder evals | consult repo | PR touching `themefinder/**`, manual dispatch |
| Backend tests | consult repo (existing) | PR/push touching `backend/**` or `themefinder/**` |
| Pre-commit | consult repo (existing) | Merged config |
| Docker builds | consult repo (existing) | Push (all 4 images) |
| Auto-sync to public repo | consult repo | Push to main touching `themefinder/**` |
| Docs deploy | public themefinder repo | Push to main (via auto-sync) |
| PyPI publish | public themefinder repo | Release tag (manual) |

## PyPI Release Process (After Migration)

1. Bump version in `consult/themefinder/pyproject.toml`, merge to main
2. The sync workflow auto-pushes to the public themefinder repo
3. Create a GitHub release on `i-dot-ai/themefinder` with matching tag (e.g. `v0.9.0`)
4. The existing `deploy-pypi.yml` builds and publishes to PyPI

Day-to-day, you never think about the public repo — it stays in sync automatically.

## Risks and Mitigations

- **uv.lock conflict**: The old `backend/uv.lock` must be deleted before generating the workspace root lockfile. uv workspaces use a single root-level lockfile.
- **Python version**: Backend requires >=3.12, themefinder allows >=3.10. No conflict — the workspace resolves to 3.12+.
- **Docker build context size**: Adding themefinder source increases context. Mitigated by `.dockerignore` excluding evals/docs/tests from production builds.
- **Secrets duplication**: Eval secrets must be copied from the themefinder repo to consult. Document which secrets are shared vs. new.
- **Subtree sync failures**: If the sync workflow fails (e.g. merge conflicts), it will need manual intervention. The force-push approach avoids this but means the public repo's git history is rewritten on each sync. This is acceptable since development happens in consult.
