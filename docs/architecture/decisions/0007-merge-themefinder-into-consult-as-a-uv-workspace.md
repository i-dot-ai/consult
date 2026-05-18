# 7. Merge themefinder into consult as a uv workspace

Date: 2026-05-01

## Status

Proposed

## Context

ThemeFinder lives in a separate public repository ([i-dot-ai/themefinder](https://github.com/i-dot-ai/themefinder)) and is consumed by consult as a PyPI dependency. In practice, consult is themefinder's only real consumer: the backend and both pipeline scripts (`pipeline-sign-off`, `pipeline-mapping`) import its internals directly.

The two-repo split forces a heavy release dance for any change that spans both projects (edit themefinder → cut a PyPI release → bump pins in consult → rebuild four Docker images), which biases against making themefinder changes in tandem with consult work. It also leaves room for version drift: each Docker image resolves themefinder independently at build time rather than from a shared lock.

ThemeFinder is still useful to publish to PyPI for external users (other government teams, researchers). Any restructuring needs to preserve PyPI publishability and keep historic release tags discoverable.

## Decision

We will move themefinder into consult as a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) member, alongside the backend and the two pipelines. The public `i-dot-ai/themefinder` repo will be archived with a redirect notice; PyPI releases will be cut from consult going forward.

1. **Single workspace, four packages.** `consult/` becomes a uv workspace whose members are `backend/`, `themefinder/`, `pipeline-sign-off/`, and `pipeline-mapping/`. A single root `pyproject.toml` declares the workspace; a single root `uv.lock` resolves dependencies for all four members together.
2. **ThemeFinder stays publishable from consult.** Its `pyproject.toml` is preserved unchanged so `pip install themefinder` continues to work for external users. Internal consumers reference it through `[tool.uv.sources] themefinder = { workspace = true }`, which uv installs editable. A `deploy-pypi.yml` workflow in consult publishes new releases on tag push.
3. **Pipelines become workspace members.** Today both pipelines pull their dependency set transitively through `themefinder>=0.8.2`. After migration, each pipeline's `pyproject.toml` lists its dependencies explicitly, and its Dockerfile is rewritten as a multi-stage uv build mirroring `backend/Dockerfile`.
4. **Archive the public repo with a redirect notice.** The public `i-dot-ai/themefinder` repo is archived (read-only). Its README is updated to point to `i-dot-ai/consult` for development, issues, and new releases. Historic source code and PyPI release tags remain browseable on the archive; external users continue to install from PyPI unchanged.

### Alternatives considered

- **Keep the pipelines on `pip install -r requirements.txt`.** Rejected: leaves two dependency-management tools coexisting in one monorepo and pipeline dependencies unlocked.
- **Git subtree import (preserving themefinder history inside consult).** Rejected: the histories don't share roots, the import would balloon consult's history, and PyPI release tags can stay attached to the public-repo commits regardless.
- **Public mirror via subtree sync.** Rejected: adds a force-pushing sync workflow and a PAT secret for no practical gain. External users can still read source on the archived repo, file issues against consult, and install from PyPI. Archiving with a redirect notice is the standard pattern for this kind of consolidation (e.g. `googleapis/python-bigquery` → `googleapis/google-cloud-python`).

## Consequences

### Positive

- **Single-PR cross-cutting changes.** Edits that span themefinder and consult become one review, one merge, one deploy.
- **No silent version drift.** A single root `uv.lock` guarantees backend and both pipelines run identical themefinder code.
- **Faster local dev loop.** Workspace members install editable, so a change in `themefinder/src/` is immediately visible to backend tests and pipeline scripts.
- **One CI surface to maintain.** ThemeFinder's tests, evals, and pre-commit move into consult, replacing three separately-evolved workflow sets.

### Negative

- **The migration PR is unavoidably large and atomic.** `build-gh.yml` builds four Docker images from repo-root context on every push, so the workspace wiring, all four Dockerfiles, the Makefile, and the CI workflows must land together.
- **Editable installs require runtime source.** uv writes a `.pth` file pointing at `themefinder/src/`, so all three Python images must copy `themefinder/src/` and `themefinder/pyproject.toml` into their **runtime** stage, not just the build stage.
- **Future themefinder source history lives only in consult.** Once the public repo is archived, new commits to `themefinder/` are only visible inside consult. Pre-archive history and release tags remain readable on the archived repo.

### Neutral

- **External users are unaffected at install time.** `pip install themefinder` continues to work; the package is published from consult to the same PyPI project. Issues and PRs are redirected to consult via the archived repo's README.
- **PyPI release process moves to consult.** Bump `themefinder/pyproject.toml`, merge, tag the release in consult; `deploy-pypi.yml` publishes. One repo, one release flow.
