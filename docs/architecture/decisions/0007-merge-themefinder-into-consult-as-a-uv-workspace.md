# 7. Merge themefinder into consult as a uv workspace

Date: 2026-05-01

## Status

Proposed

## Context

ThemeFinder lives in a separate public repository ([i-dot-ai/themefinder](https://github.com/i-dot-ai/themefinder)) and is consumed by consult as a PyPI dependency. In practice, consult is themefinder's only real consumer: the backend and both pipeline scripts (`pipeline-sign-off`, `pipeline-mapping`) import its internals directly.

The two-repo split forces a heavy release dance for any change that spans both projects (edit themefinder → cut a PyPI release → bump pins in consult → rebuild four Docker images), which biases against making themefinder changes in tandem with consult work. It also leaves room for version drift: each Docker image resolves themefinder independently at build time rather than from a shared lock.

ThemeFinder is still useful to publish to PyPI for external users (other government teams, researchers). Any restructuring needs to preserve PyPI publishability and keep release tags discoverable.

## Decision

We will move themefinder into consult as a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) member, alongside the backend and the two pipelines.

1. **Single workspace, four packages.** `consult/` becomes a uv workspace whose members are `backend/`, `themefinder/`, `pipeline-sign-off/`, and `pipeline-mapping/`. A single root `pyproject.toml` declares the workspace; a single root `uv.lock` resolves dependencies for all four members together.
2. **ThemeFinder stays publishable.** Its `pyproject.toml` is preserved unchanged so `pip install themefinder` continues to work for external users. Internal consumers reference it through `[tool.uv.sources] themefinder = { workspace = true }`, which uv installs editable.
3. **Pipelines become workspace members.** Today both pipelines pull their dependency set transitively through `themefinder>=0.8.2`. After migration, each pipeline's `pyproject.toml` lists its dependencies explicitly, and its Dockerfile is rewritten as a multi-stage uv build mirroring `backend/Dockerfile`.
4. **Public mirror via subtree sync.** The public `i-dot-ai/themefinder` repo is preserved as a published mirror. A GitHub Actions workflow in consult runs `git subtree split --prefix=themefinder` and force-pushes to the public repo on every change to `themefinder/**`. The public repo retains `deploy-pypi.yml` and `deploy-docs.yml`; its tests, evals, and pre-commit are deleted because those checks now run inside consult.

### Alternatives considered

- **Keep the pipelines on `pip install -r requirements.txt`.** Rejected: leaves two dependency-management tools coexisting in one monorepo and pipeline dependencies unlocked.
- **Git subtree import (preserving themefinder history inside consult).** Rejected: the histories don't share roots, the import would balloon consult's history, and PyPI release tags can stay attached to the public-repo commits regardless. Subtree is used only for the outbound sync.
- **Archive the public themefinder repo entirely.** Rejected: external users install from PyPI and may want to read source or file issues. Keeping a synced mirror is cheap.

## Consequences

### Positive

- **Single-PR cross-cutting changes.** Edits that span themefinder and consult become one review, one merge, one deploy.
- **No silent version drift.** A single root `uv.lock` guarantees backend and both pipelines run identical themefinder code.
- **Faster local dev loop.** Workspace members install editable, so a change in `themefinder/src/` is immediately visible to backend tests and pipeline scripts.
- **One CI surface to maintain.** ThemeFinder's tests, evals, and pre-commit move into consult, replacing three separately-evolved workflow sets.

### Negative

- **The migration PR is unavoidably large and atomic.** `build-gh.yml` builds four Docker images from repo-root context on every push, so the workspace wiring, all four Dockerfiles, the Makefile, and the CI workflows must land together.
- **Editable installs require runtime source.** uv writes a `.pth` file pointing at `themefinder/src/`, so all three Python images must copy `themefinder/src/` and `themefinder/pyproject.toml` into their **runtime** stage, not just the build stage.
- **Public repo history is rewritten on every sync.** `git subtree split` followed by `git push --force` produces a new linear history each time. Existing PyPI release tags remain attached to their commits, but new releases land on the rewritten history.
- **PyPI release gains a step.** A version bump must merge to consult main, propagate via the sync workflow, and then a release tag is cut on the public repo to fire `deploy-pypi.yml`.

### Neutral

- **External users are unaffected.** PyPI installs, README links, and existing release tags continue to work. Issues and PRs against the public repo are redirected to consult.
