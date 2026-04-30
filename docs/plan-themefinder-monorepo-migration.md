# Plan: Move ThemeFinder into Consult as a Monorepo

> **Updated 2026-04-30.** This supersedes the original 2026-04-08 plan. The shape of the migration (uv workspace, 3 PRs, subtree sync to public repo) is unchanged. The deltas are in the **Changes since original plan** section at the bottom — read those first if you've seen the prior version.

## Context

Today, getting a themefinder change into consult requires: edit themefinder → bump version → merge → PyPI release → update version pins in consult → rebuild Docker images → deploy. Two repos, two PRs, a PyPI release, and four Docker builds for what might be a one-line prompt change.

The two projects are tightly coupled — consult's pipeline scripts import themefinder internals (`themefinder.llm.OpenAILLM`, `themefinder.models.ThemeNode`, `themefinder.advanced_tasks.theme_clustering_agent`), and themefinder is effectively a private library with one real consumer. Moving themefinder into consult as a uv workspace member eliminates the release ceremony while keeping it publishable to PyPI for external users.

**After this migration, the dev loop becomes:** edit themefinder → it's immediately available in backend and pipelines → run tests → commit → single PR.

## Snapshot of current state (2026-04-30)

- **consult** main: `0c4e78f86`. No root `pyproject.toml` / `uv.lock`. Backend uses `[dependency-groups]` (PEP 735) for dev deps. `requires-python = ">=3.12,<3.13"`. `[tool.uv] exclude-newer = "P14D"`. Dockerfiles for `backend`, `pipeline-sign-off`, `pipeline-mapping` all build from repo-root context. `build-gh.yml` builds all 4 services (`pipeline-mapping,pipeline-sign-off,backend,frontend`) on every push.
- **themefinder** main: `312510d`. `requires-python = ">=3.10,<3.13"`. Uses `[project.optional-dependencies] dev = [...]` and `docs = [...]` (PEP 621 extras), not `[dependency-groups]`. Has its own `uv.lock` and `.python-version` (3.12). New top-level file `setup_consultation.py` (a CLI tool, in coverage omit). Pre-commit includes ruff + ruff-format (newer than consult's pre-commit config).
- Both pipeline scripts still import themefinder internals (`themefinder.llm.OpenAILLM`, `themefinder.models.ThemeNode`, `themefinder.advanced_tasks.theme_clustering_agent.ThemeClusteringAgent`, plus the `rule_*_slack` functions and the `theme_*` async functions).
- Pipeline `requirements.txt` files contain a single line: `themefinder>=0.8.2`; pipelines currently install with `pip install -r requirements.txt` and use `python:3.11-slim-bullseye`. After migration, the pipelines become **uv workspace members** alongside `backend` and `themefinder`, with their own `pyproject.toml`. The `requirements.txt` files are deleted.

## Target Directory Structure

```
consult/
├── pyproject.toml              ← NEW: root workspace config (uv workspace only, not a package)
├── uv.lock                     ← NEW: single lockfile for the whole workspace
├── .python-version             ← NEW: 3.12 (matches both backend and themefinder constraints)
├── Makefile
├── docker-compose.yml
├── Procfile.dev
├── backend/
│   ├── pyproject.toml          ← MODIFIED: themefinder as workspace dependency
│   ├── Dockerfile              ← MODIFIED: copy workspace + themefinder into build AND runtime stages
│   └── ...
├── frontend/
├── themefinder/                ← NEW: copied (not subtree) from public repo
│   ├── pyproject.toml          ← KEPT: unchanged (still publishable to PyPI; setuptools build, [project.optional-dependencies])
│   ├── src/themefinder/
│   ├── tests/
│   ├── evals/
│   ├── docs/
│   ├── examples/
│   ├── setup_consultation.py   ← KEPT: themefinder CLI tool
│   ├── Makefile                ← KEPT (renamed targets handled in PR1: see Phase 3)
│   └── ...
├── pipeline-sign-off/
│   ├── pyproject.toml          ← NEW: workspace member; deps + themefinder = workspace
│   ├── Dockerfile              ← REWRITTEN: uv-based, multi-stage, mirrors backend
│   ├── find_themes_script.py
│   └── requirements.txt        ← DELETED
├── pipeline-mapping/
│   ├── pyproject.toml          ← NEW: workspace member; deps + themefinder = workspace
│   ├── Dockerfile              ← REWRITTEN: uv-based, multi-stage, mirrors backend
│   ├── assign_themes_script.py
│   └── requirements.txt        ← DELETED
└── .github/workflows/
    ├── themefinder-ci.yml      ← NEW: tests + 95% coverage
    ├── themefinder-eval.yml    ← NEW: LLM evals (moved from public repo)
    ├── sync-themefinder.yml    ← NEW: auto-push subtree to public repo
    ├── backend-ci.yml          ← MODIFIED: also trigger on themefinder/** changes; sync from root
    └── ... (existing workflows unchanged)
```

## PR Structure

The migration is split into 3 PRs. Phases 1–3 must land together because `build-gh.yml` builds all 4 images on every push — a half-migrated state breaks builds.

| PR | Phases | What | Can merge independently? |
|---|---|---|---|
| **PR 1** | 1 + 2 + 3 | Core migration: copy themefinder, workspace config, Dockerfiles, Makefile | Atomic: must land as one |
| **PR 2** | 4 | CI: themefinder-ci.yml, themefinder-eval.yml, backend-ci.yml triggers, merged pre-commit | After PR 1 |
| **PR 3** | 5 | Public repo sync: sync workflow + token + README updates | After PR 1 |

## Implementation Checklist

### PR 1: Core Migration

#### Phase 1: Copy and wire up the workspace

- [ ] Copy themefinder repo contents into `consult/themefinder/` (exclude `.git/`, `.github/`). Keep themefinder's `pyproject.toml`, `Makefile`, `mkdocs.yml`, `setup_consultation.py`, `.python-version`, `.adr-dir`, README/LICENCE.
- [ ] Delete themefinder's `uv.lock` from the copied subdir (workspace uses one root lockfile).
- [ ] Create root `consult/pyproject.toml` as workspace-only (no `[project]`, just workspace config):
  ```toml
  [tool.uv.workspace]
  members = ["backend", "themefinder", "pipeline-sign-off", "pipeline-mapping"]

  [tool.uv]
  exclude-newer = "P14D"
  ```
- [ ] Create root `consult/.python-version` containing `3.12`.
- [ ] Update `backend/pyproject.toml` — declare workspace source for themefinder:
  ```toml
  [tool.uv.sources]
  themefinder = { workspace = true }
  ```
  Remove `[tool.uv] exclude-newer = "P14D"` from `backend/pyproject.toml` (now lives at root).
- [ ] Delete `backend/uv.lock`.
- [ ] **Create `pipeline-sign-off/pyproject.toml`** as a workspace member. Deps inferred from `find_themes_script.py` imports (`themefinder`, `boto3`, `pandas`, `urllib3`, `openai`, `pydantic`):
  ```toml
  [project]
  name = "pipeline-sign-off"
  version = "0.1.0"
  requires-python = ">=3.12,<3.13"
  dependencies = [
    "themefinder",
    "boto3>=1.42.17",
    "pandas>=2.2.2",
    "urllib3>=2.0.0",
    "openai>=2.14.0",
    "pydantic>=2.12.5",
  ]

  [tool.uv.sources]
  themefinder = { workspace = true }

  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"

  [tool.hatch.build.targets.wheel]
  only-include = ["find_themes_script.py"]
  ```
  *Note: pin versions to whatever resolves cleanly under root `exclude-newer = "P14D"`. The build-system entry exists so uv can install the package editable; `only-include` keeps the wheel minimal.*
- [ ] **Create `pipeline-mapping/pyproject.toml`** with the same shape but `name = "pipeline-mapping"` and deps inferred from `assign_themes_script.py` imports (subset: themefinder, boto3, pandas, urllib3 — verify before pinning).
- [ ] Delete `pipeline-sign-off/requirements.txt` and `pipeline-mapping/requirements.txt`.
- [ ] Run `uv lock` from repo root to generate `consult/uv.lock`. Then `uv sync --all-packages --all-extras --group dev` to install everything (all 4 workspace members + themefinder's `dev`/`docs` extras + backend's `dev` group).
- [ ] Verify resolution didn't break under `exclude-newer = "P14D"`. If themefinder needs an older pin not within the 14-day window, raise to root (decision required: relax constraint or upgrade pin).
- [ ] Verify: `uv run python -c "from themefinder.models import ThemeNode; print('ok')"`.
- [ ] Verify: `make test-backend` passes from repo root.

#### Phase 2: Update Dockerfiles

The build context for all 4 images is the repo root (set in `build-gh.yml` via `i-dot-ai-core-github-actions/build-docker.yml`). Workspace members install editable, so **themefinder source must be present in the runtime image too** — not just at build time — because the venv contains a `.pth` file pointing at `/src/themefinder/src`.

**`backend/Dockerfile`** — both stages need workspace + themefinder source:
- [ ] `uv-packages` stage (currently `WORKDIR /src/backend; COPY ./backend/pyproject.toml ./backend/uv.lock ./`): replace with workspace-aware copy:
  ```dockerfile
  WORKDIR /src
  COPY pyproject.toml uv.lock .python-version ./
  COPY themefinder/pyproject.toml ./themefinder/
  COPY themefinder/src/ ./themefinder/src/
  COPY backend/pyproject.toml ./backend/
  WORKDIR /src/backend
  ENV UV_PROJECT_ENVIRONMENT=venv
  RUN uv sync --frozen --no-install-project
  ```
- [ ] Runtime stage (currently `COPY ./backend ./backend` and `COPY --from=uv-packages /src/backend/venv ./backend/venv`): also copy themefinder pyproject + src so editable install resolves at runtime:
  ```dockerfile
  WORKDIR /src
  COPY ./backend ./backend
  COPY ./themefinder/pyproject.toml ./themefinder/
  COPY ./themefinder/src ./themefinder/src
  COPY --from=uv-packages /src/backend/venv ./backend/venv
  ```

**`pipeline-sign-off/Dockerfile`** and **`pipeline-mapping/Dockerfile`** — rewrite as multi-stage uv-based builds, mirroring `backend/Dockerfile`. Bumps base image from `python:3.11-slim-bullseye` to `python:3.12-slim` (workspace lock targets 3.12). Editable install applies here too — runtime stage must include workspace root + themefinder source + the pipeline's own pyproject:
  ```dockerfile
  # uv-packages stage: build the venv
  FROM public.ecr.aws/docker/library/python:3.12-slim AS uv-packages

  COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

  WORKDIR /src
  COPY pyproject.toml uv.lock .python-version ./
  COPY themefinder/pyproject.toml ./themefinder/
  COPY themefinder/src/ ./themefinder/src/
  COPY pipeline-sign-off/pyproject.toml ./pipeline-sign-off/
  COPY pipeline-sign-off/find_themes_script.py ./pipeline-sign-off/

  WORKDIR /src/pipeline-sign-off
  ENV UV_PROJECT_ENVIRONMENT=venv
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
  ```
- [ ] `pipeline-mapping/Dockerfile` follows the same pattern with `pipeline-mapping` and `assign_themes_script.py` substituted throughout.
- [ ] Delete `pipeline-sign-off/requirements.txt` and `pipeline-mapping/requirements.txt`.

**`.dockerignore`** — exclude themefinder paths not needed at runtime:
- [ ] Add lines: `themefinder/evals/`, `themefinder/docs/`, `themefinder/tests/`, `themefinder/examples/`, `themefinder/setup_consultation.py`.

**Verification:**
- [ ] `make docker_build_local service=backend` succeeds.
- [ ] `make docker_build_local service=pipeline-sign-off` succeeds.
- [ ] `make docker_build_local service=pipeline-mapping` succeeds.
- [ ] Run a built backend image and verify Django boots.
- [ ] Run pipeline images with `--help` flag (or equivalent dry-run) to confirm imports resolve.

#### Phase 3: Update Makefile and local dev

- [ ] Change `make install` from `cd backend && uv sync` to `uv sync --all-packages --all-extras --group dev` (run from repo root). One command now installs backend, themefinder, and both pipelines.
- [ ] Update `make test-backend`: drop `cd backend && PYTHONPATH=..` if root-level `uv run` works (the workspace lets `uv run pytest --rootdir=backend backend/tests/` resolve from root). If tests rely on `PYTHONPATH=..`, leave the cd in place and use `cd backend && uv run pytest tests/ --random-order`.
- [ ] Add `make test-themefinder` target: `uv run --package themefinder pytest themefinder/tests/ -v`.
- [ ] Add `make test-all` target combining backend, frontend, and themefinder.
- [ ] Add `make run-evals` target: `cd themefinder/evals && uv run python benchmark.py --quick`.
- [ ] Optional: add `make run-pipeline-sign-off` / `make run-pipeline-mapping` targets that exercise each script via `uv run --package pipeline-sign-off python find_themes_script.py --help` (sanity check that workspace wiring works locally).
- [ ] Update `check-python-code` / `format-python-code` if you want them to also lint themefinder + pipelines (decision required — see Risks).
- [ ] Verify: `make serve` boots cleanly with workspace install.
- [ ] Verify: `make test-themefinder` passes.

### PR 2: CI Migration

#### `themefinder-ci.yml` (new)

Mirrors the current `themefinder/.github/workflows/tests.yml` but path-scoped:
- [ ] Triggers: `pull_request` and `push: branches: [main]` with `paths: ['themefinder/**', '.github/workflows/themefinder-ci.yml']`.
- [ ] Matrix: `python-version: ['3.10', '3.11', '3.12']` — themefinder still publishes to PyPI for those versions, so we keep matrix coverage.
- [ ] `astral-sh/setup-uv` pinned to the same SHA themefinder uses (`08807647e7069bb48b6ef5acd8ec9567f424441b`).
- [ ] `uv sync --package themefinder --extra dev --extra docs` (or `--all-extras --package themefinder`).
- [ ] `uv run --package themefinder coverage run -m pytest -v -s` (cwd = `themefinder/`).
- [ ] `uv run --package themefinder coverage report -m --fail-under=95`.

#### `themefinder-eval.yml` (new)

Port of the public repo's `eval.yml`. Self-hosted EC2 runner via `i-dot-ai/i-dot-ai-core-github-actions` — these secrets already exist in the consult repo (used by `build-gh.yml`):
- [ ] Trigger paths: `themefinder/evals/**`, `themefinder/src/themefinder/**`, `.github/workflows/themefinder-eval.yml`.
- [ ] `workflow_dispatch` inputs: `dataset` (string, default `gambling_XS`) and `eval_type` (choice: generation/mapping/condensation/refinement/all, default `generation`).
- [ ] Update working dir to `themefinder/evals` instead of `evals`.
- [ ] Update install step to `uv sync --package themefinder --extra dev` (or whatever ends up needed).

**Secrets needed in consult (only add if not already present):**

| Secret | Already in consult? | Notes |
|---|---|---|
| `AWS_GITHUBRUNNER_USER_ACCESS_KEY` | ✅ | Used by `build-gh.yml` |
| `AWS_GITHUBRUNNER_USER_SECRET_ID` | ✅ | Used by `build-gh.yml` |
| `AWS_GITHUBRUNNER_PAT` | ✅ | Used by `build-gh.yml` |
| `AWS_REGION` | ✅ | Used by `build-gh.yml` |
| `AWS_ACCOUNT_ID` | ✅ | Used by `build-gh.yml` |
| `AZURE_OPENAI_ENDPOINT` | ❌ copy from themefinder | |
| `AZURE_OPENAI_API_KEY` | ❌ | |
| `AZURE_OPENAI_API_VERSION` | ❌ | |
| `LLM_GATEWAY_URL` | ❌ | |
| `CONSULT_EVAL_LITELLM_API_KEY` | ❌ | |
| `LOCAI_ENDPOINT` | ❌ | |
| `LOCAI_API_KEY` | ❌ | |
| `AUTO_EVAL_4_1_SWEDEN_DEPLOYMENT` | ❌ | |
| `LANGFUSE_SECRET_KEY` | ❌ | |
| `LANGFUSE_PUBLIC_KEY` | ❌ | |
| `LANGFUSE_BASE_URL` | ❌ | |
| `THEMEFINDER_S3_BUCKET_NAME` | ❌ | |
| `HF_TOKEN` | ❌ | **New** since original plan — used by sentence-transformers |
| `SLACK_WEBHOOK_URL` | Check (consult may already have one) | If consult already has a different webhook, keep two distinct secret names |

- [ ] Create a GitHub `eval` environment in the consult repo to scope these secrets, mirroring themefinder's setup.

#### `backend-ci.yml` (modified)

- [ ] Add `themefinder/**` and `pyproject.toml` and `uv.lock` to trigger paths (so backend CI re-runs when shared deps change).
- [ ] Change `uv sync --all-extras` (cwd backend) → `uv sync --all-packages --all-extras --group dev` from root, or `uv sync --package consult --all-extras --group dev` from root.
- [ ] Verify backend CI step `uv run python manage.py migrate` still works with workspace venv path.

#### Pre-commit merge

Consult's `.pre-commit-config.yaml` and themefinder's differ in versions, hook set, and exclude patterns. Merged config:

- [ ] Bump `pre-commit-hooks` to `v6.0.0` (themefinder's version; superset).
- [ ] Bump `detect-secrets` to `v1.5.0`. Combine excludes: `(uv.lock|.env.example|.env.test|^.github/workflows/|\.cruft\.json)` (themefinder used `poetry.lock`; replace with `uv.lock` since the monorepo uses uv).
- [ ] Keep `bandit` (consult-only, scoped `^backend/.*\.py$`).
- [ ] Keep `mypy` (consult-only — themefinder doesn't use it).
- [ ] Add `ruff` + `ruff-format` from themefinder, **scoped to `^themefinder/`** so we don't surprise the consult team by enforcing ruff format on backend code (consult currently runs ruff via the Makefile, not pre-commit). Decision required: do we want ruff at root scope eventually? Captured as a follow-up.
- [ ] Bump `nbstripout` to `0.9.1`.
- [ ] Keep the local `detect-ip` and `detect-aws-account` hooks.
- [ ] `run_precommit.yml` already uses `python-version-file: 'backend/pyproject.toml'`. That's fine, no change needed.

### PR 3: Public Repo Sync

- [ ] Create `.github/workflows/sync-themefinder.yml`:
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
        - uses: actions/checkout@v6
          with:
            fetch-depth: 0
        - name: Push themefinder subtree to public repo
          run: |
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git remote add themefinder https://x-access-token:${{ secrets.THEMEFINDER_PUSH_TOKEN }}@github.com/i-dot-ai/themefinder.git
            git subtree split --prefix=themefinder -b themefinder-sync
            git push themefinder themefinder-sync:main --force
  ```
- [ ] Create `THEMEFINDER_PUSH_TOKEN` secret in consult repo (GitHub PAT with push access to `i-dot-ai/themefinder`).
- [ ] In the public `i-dot-ai/themefinder` repo: keep `deploy-pypi.yml` (release-tag triggered) and `deploy-docs.yml` (push-to-main triggered, fires automatically after each sync). **Delete `tests.yml`, `eval.yml`, `pre-commit.yml` from the public repo** to avoid duplicate work — those run in consult now.
- [ ] Update public repo README: development happens in `i-dot-ai/consult`; this repo is a published mirror. Issues + PyPI releases still happen here.
- [ ] Verify: merge a no-op `themefinder/` change to consult main; confirm it appears in public repo and `deploy-docs.yml` succeeds.
- [ ] Document the PyPI release process in consult `docs/`: bump version in `consult/themefinder/pyproject.toml` → merge to main → wait for sync → create release on public repo with tag matching version → `deploy-pypi.yml` fires.

## Workflow Locations After Migration

| Workflow | Location | Trigger |
|---|---|---|
| ThemeFinder tests + coverage | consult repo | PR/push touching `themefinder/**` |
| ThemeFinder evals | consult repo | PR touching `themefinder/{evals,src}/**`, manual dispatch |
| Backend tests | consult repo (existing) | PR/push touching `backend/**`, `themefinder/**`, `pyproject.toml`, `uv.lock` |
| Pre-commit | consult repo (existing, with merged config) | PR/push to main |
| Docker builds (4 images) | consult repo (existing) | Every push |
| Auto-sync to public repo | consult repo | Push to main touching `themefinder/**` |
| Docs deploy | public themefinder repo (kept) | Push to main (fires after auto-sync) |
| PyPI publish | public themefinder repo (kept) | Release tag (manual) |

## Risks and Mitigations

1. **PEP 621 extras vs PEP 735 groups inconsistency.** Themefinder uses `[project.optional-dependencies]` (so `dev`/`docs` are part of the published wheel's metadata — this is a feature, since PyPI users can `pip install themefinder[dev]`). Consult uses `[dependency-groups]` (PEP 735, not published). Workspace install needs both: `uv sync --all-packages --all-extras --group dev`. Verified that `uv` resolves this correctly. *Don't* convert themefinder to dependency-groups — it would break PyPI users.

2. **Editable install at runtime in Docker.** uv installs workspace members editable; the venv has a `.pth` file pointing at `/src/themefinder/src`. **All three Python images** (`backend`, `pipeline-sign-off`, `pipeline-mapping`) must therefore copy `themefinder/src/` and `themefinder/pyproject.toml` into the runtime stage, not just the venv. The original plan only updated the `uv-packages` stage — easy to miss. Phase 2 above calls this out for each Dockerfile.

3. **`exclude-newer = "P14D"` may break themefinder resolution.** Some themefinder pins (e.g. `protobuf==6.33.5`, `cryptography>=46.0.7`) might fall outside a 14-day window if the workspace lock is regenerated against fresh indexes. Mitigation: when Phase 1 lock fails, raise `exclude-newer` or pin the affected dep. Decision should be deliberate (the constraint exists for supply-chain reasons).

4. **Pre-commit version conflicts.** Themefinder uses newer hook revs (pre-commit-hooks v6.0.0, detect-secrets v1.5.0, nbstripout 0.9.1) than consult (v4.4.0, v1.4.0, 0.7.1). Bumping to themefinder's revs is the path of least resistance but could surface new lint errors in consult code — run pre-commit on the merged config locally before opening PR 2.

5. **Ruff scoping.** Themefinder's pre-commit runs ruff project-wide; consult deliberately runs ruff only via the Makefile. PR 2 scopes the ruff hooks to `^themefinder/` to avoid changing consult's lint policy in a CI PR. A follow-up decision: do we want ruff at root scope?

6. **Subtree force-push rewrites public repo history.** Each sync is `git subtree split` then `git push --force`. PyPI release tags stay attached to the commits they were cut from, but new releases land on a new history. Acceptable because development now happens in consult; document this in the public repo README.

7. **Eval workflow secret duplication.** Many secrets need copying from themefinder repo to consult. Use a GitHub `eval` environment in consult to scope them (matching themefinder's setup). Some AWS_* secrets already exist in consult — reuse, don't duplicate.

8. **Build context size.** Adding `themefinder/` to the Docker build context inflates context size for backend + 2 pipeline images. `.dockerignore` excludes evals/docs/tests/examples/setup_consultation.py from production builds.

9. **`setup_consultation.py` retention.** This file lives at themefinder repo root and is referenced by themefinder's Makefile target and coverage omit. After move, it sits at `themefinder/setup_consultation.py` — both relative paths still work because they're resolved from `themefinder/` cwd. No code change needed; just don't drop the file during the copy.

10. **Backend tests' `PYTHONPATH=..` dependency.** Consult's `Makefile` runs backend pytest as `cd backend && PYTHONPATH=.. uv run pytest tests/`. The `PYTHONPATH=..` exists for a reason (likely to expose top-level packages like `lambda/` or imports across the repo). Don't drop this without checking — verify in Phase 3.

11. **Pipelines becoming workspace members is a structural change.** Pipelines previously had no `pyproject.toml` and pulled their dep set transitively through `themefinder>=0.8.2`. After migration each pipeline declares its own deps explicitly, locked under the root `uv.lock`. Implications: (a) version drift between backend and pipelines can no longer happen silently — a single resolution must satisfy all four packages, which is the point but may surface conflicts on Phase 1 lock; (b) the inferred dep list (`boto3`, `pandas`, `urllib3`, `openai`, `pydantic`) must be verified against `find_themes_script.py` and `assign_themes_script.py` imports — a missed import will only surface at runtime. (c) Bumps base image from `python:3.11-slim-bullseye` to `python:3.12-slim` to match the workspace lock; smoke-test the built images against AWS Lambda / ECR target environment before merging.

## Changes since the original plan (2026-04-08 → 2026-04-30)

The 3-PR shape and the workspace approach are unchanged. Concrete deltas:

**Themefinder has moved on:**
- Added explicit deps: `tenacity>=8.0.0`, `tiktoken>=0.5.0`. Pinned `protobuf==6.33.5`. Bumped `cryptography>=46.0.7` (security).
- New top-level file `setup_consultation.py` (a CLI tool used by themefinder consumers; in coverage omit). Plan now calls out preserving this in the copy step.
- Themefinder pre-commit gained `ruff` + `ruff-format` and bumped hook revs. Original plan said "merge detect-secrets and nbstripout"; the actual merge is larger and ruff scoping is a new decision point.
- Removed `requirements*.txt` files from themefinder; uses `uv` exclusively. (Doesn't change the migration but means there's no "unify requirements" step.)
- Removed `langchain` from evals (uses OpenAI SDK directly). Smaller eval dep tree, but no plan-level change.
- `eval.yml` workflow added a new `HF_TOKEN` secret (sentence-transformers download). Added to the secret-copy list above.
- `setup-uv` now pinned to a specific SHA (`08807647...`). PR 2 should match.
- `.python-version` is `3.12`; matches what we'll set at consult root.
- Coverage gate on themefinder is `--fail-under=95` (already in original plan, confirmed unchanged).

**Consult-side state to be aware of:**
- Backend CI uses `uv sync --all-extras` from `./backend`. Plan now specifies the workspace-aware replacement.
- `[tool.uv] exclude-newer = "P14D"` exists at backend pyproject and needs to migrate to root pyproject. Documented as risk #3.
- `build-gh.yml` builds 4 services from repo-root context — confirms PR 1 must be atomic. Unchanged from original plan.
- `run_precommit.yml` reads python version from `backend/pyproject.toml`; that file remains so no change needed.

**Departure from the original plan: pipelines now use uv too.**
- Original plan kept the pipelines on `pip install -r requirements.txt` and added a single `pip install ./themefinder` line. That left two dependency-management tools (pip + uv) in the same monorepo and meant pipeline deps were unlocked.
- New approach (this revision): both pipelines become **uv workspace members** with their own `pyproject.toml`. `requirements.txt` files are **deleted entirely**. Dockerfiles are rewritten as multi-stage uv builds mirroring `backend/Dockerfile`. One `uv.lock` covers all four images. Bumps pipeline base image from `python:3.11-slim-bullseye` to `python:3.12-slim` to match the workspace's resolved Python.
- New risk surfaced by this change: pipeline imports must be enumerated explicitly in each pipeline's `pyproject.toml` (see risk #11). Previously they were inherited transitively through themefinder.

**New risks documented:**
- Editable install runtime requirement (risk #2).
- `exclude-newer` may force pin renegotiation (risk #3).
- Ruff scoping decision (risk #5).
- PEP 621 vs PEP 735 install-flag specifics (risk #1).
- Pipelines as workspace members + base image bump (risk #11).

**Trimmed from original plan:**
- "Remove themefinder>=0.8.2 from requirements.txt" — superseded; `requirements.txt` files are deleted outright.
- Original plan listed pre-commit merge as a one-liner; now expanded with concrete version + scope decisions.
