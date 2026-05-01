# 7. Merge themefinder into consult as a uv workspace

Date: 2026-05-01

## Status

Proposed

## Context

ThemeFinder lives in a separate public repository ([i-dot-ai/themefinder](https://github.com/i-dot-ai/themefinder)) and is consumed by consult as a PyPI dependency. In practice, consult is themefinder's only real consumer: the pipeline scripts (`pipeline-sign-off`, `pipeline-mapping`) import its internals directly (`themefinder.llm.OpenAILLM`, `themefinder.models.ThemeNode`, `themefinder.advanced_tasks.theme_clustering_agent.ThemeClusteringAgent`), and the backend depends on it through the same pipelines.

The two-repo split imposes a heavy release ceremony for changes that span both projects. Today, getting a one-line themefinder change into consult requires:

1. Edit themefinder, open a PR, get it reviewed and merged
2. Bump the themefinder version
3. Cut a PyPI release
4. Bump the themefinder version pin in consult's `requirements.txt` / `pyproject.toml`
5. Open a second PR in consult, get it reviewed and merged
6. Rebuild four Docker images and redeploy

This friction biases against making themefinder changes in tandem with consult work — even when the change is unambiguously needed by consult and has no external consumer who would notice. It also means version drift between the backend and the two pipelines is possible whenever they get rebuilt at different times, since each pulls themefinder transitively rather than from a shared lock.

ThemeFinder is, however, still useful to publish to PyPI for external users (research teams who want to use the library standalone). Any restructuring needs to preserve PyPI publishability and keep public release tags discoverable, even if the canonical development location moves.

A separate planning document captures the full migration mechanics: [`docs/plan-themefinder-monorepo-migration.md`](../../plan-themefinder-monorepo-migration.md).

## Decision

We will move themefinder into consult as a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) member, alongside the backend and the two pipelines. Concretely:

1. **Single workspace, four packages.** `consult/` becomes a uv workspace whose members are `backend/`, `themefinder/`, `pipeline-sign-off/`, and `pipeline-mapping/`. A single root `pyproject.toml` declares the workspace; a single root `uv.lock` resolves dependencies for all four members together.
2. **ThemeFinder stays publishable.** Its `pyproject.toml` is preserved unchanged (setuptools build, `[project.optional-dependencies]` extras), so `pip install themefinder` continues to work for external users. Internal consumers (backend, pipelines) reference it through `[tool.uv.sources] themefinder = { workspace = true }`, which uv installs editable.
3. **Pipelines become workspace members too.** Today both pipelines install with `pip install -r requirements.txt` (a single line: `themefinder>=0.8.2`) and pull their dependency set transitively through themefinder. After migration, each pipeline gets its own `pyproject.toml` enumerating its dependencies explicitly, and its Dockerfile is rewritten as a multi-stage uv build mirroring `backend/Dockerfile`. The pipeline base image bumps from `python:3.11-slim-bullseye` to `python:3.12-slim` to match the workspace Python version.
4. **Public mirror via subtree sync.** The public `i-dot-ai/themefinder` repo is preserved as a published mirror. A new GitHub Actions workflow in consult runs `git subtree split --prefix=themefinder` and force-pushes to the public repo on every change to `themefinder/**`. The public repo retains its `deploy-pypi.yml` (release-tag triggered) and `deploy-docs.yml`; its `tests.yml`, `eval.yml`, and `pre-commit.yml` are deleted because those checks now run inside consult.
5. **Migration lands as three PRs.** PR 1 is the atomic core migration (must land in one piece because `build-gh.yml` builds all four Docker images on every push, so a half-migrated state breaks the build). PR 2 ports CI workflows (themefinder tests, evals, merged pre-commit). PR 3 wires up the public-repo sync.

After this lands, the dev loop becomes: edit themefinder → it's immediately available in backend and pipelines → run tests → commit → single PR.

### Alternatives considered

- **Status quo (two repos, PyPI release on every change).** Rejected: the friction is the entire reason for this proposal, and there is no external consumer who benefits from the release cadence currently being a hard gate on internal consult work.
- **Move themefinder into consult, but keep the pipelines on pip + `requirements.txt`.** This was the original approach (the 2026-04-08 plan). Rejected on the second pass because it leaves two dependency-management tools coexisting in one monorepo, leaves pipeline dependencies unlocked, and means a single themefinder change still requires verifying three different install paths. Going all-in on uv is more work in the migration but eliminates the inconsistency permanently.
- **Git subtree (instead of a clean copy) when importing themefinder into consult.** Considered for preserving themefinder's commit history inside consult. Rejected because the two histories don't share roots, the import would balloon consult's history, and PyPI release tags can stay attached to the public-repo commits regardless. We use subtree only for the outbound sync.
- **Archive the public themefinder repo entirely.** Rejected because external users (other government teams, researchers) install from PyPI and may want to read source / file issues against the published version. Keeping a synced mirror is cheap.

## Consequences

### Positive

- **Single-PR cross-cutting changes.** Edits that span themefinder and consult become one review, one merge, one deploy — eliminating the 6-step release dance described in Context.
- **No more silent version drift.** The four Docker images previously resolved themefinder independently at build time. After migration, a single root `uv.lock` guarantees backend and both pipelines run identical themefinder code.
- **Faster local dev loop.** uv installs workspace members editable, so a code change in `themefinder/src/` is immediately visible to backend tests and pipeline scripts without any reinstall step.
- **One CI surface to maintain.** ThemeFinder's tests, evals, and pre-commit checks all move into consult, replacing three separately-evolved workflow sets.

### Negative

- **PR 1 is unavoidably large and atomic.** `build-gh.yml` builds four Docker images from repo-root context on every push, so the workspace wiring, all four Dockerfiles, and the Makefile must change in a single PR. Reviewer fatigue is a real risk; we mitigate by splitting CI and sync changes into PRs 2 and 3.
- **Editable installs require runtime source.** uv's editable install writes a `.pth` file pointing at `themefinder/src/`, so all three Python Docker images must copy `themefinder/src/` and `themefinder/pyproject.toml` into their **runtime** stage, not just the build stage. This is easy to miss and is called out explicitly in the plan.
- **Public repo history is rewritten on every sync.** `git subtree split` followed by `git push --force` produces a new linear history each time. Existing PyPI release tags remain attached to the commits they were cut from, but new releases land on the rewritten history. Acceptable because the public repo's role shifts from primary development location to published mirror — but this is documented in the public repo README so external contributors know to file PRs against consult.
- **PyPI release process gets a new step.** Bumping `themefinder/pyproject.toml` no longer suffices on its own — the change has to merge to consult main, wait for the sync workflow, then a release tag is cut on the public repo to fire `deploy-pypi.yml`. The plan documents this; we accept the extra hop because PyPI releases are infrequent compared to internal merges.
- **Resolution under `exclude-newer = "P14D"` may surface conflicts.** The 14-day index window currently scoped to `backend/pyproject.toml` migrates to the workspace root and now constrains themefinder's pins too. Some themefinder pins (`protobuf==6.33.5`, `cryptography>=46.0.7`) may fall outside the window. If the lock fails, the resolution is a deliberate decision (relax the constraint or upgrade the pin) rather than a silent regression.
- **Pipeline dependencies must be enumerated explicitly.** Previously transitive through `themefinder>=0.8.2`; now each pipeline's `pyproject.toml` must list `boto3`, `pandas`, `urllib3`, `openai`, `pydantic`, etc. explicitly. A missed import only surfaces at runtime, so the pipeline images need a smoke test before the PR merges.

### Neutral

- **External users are unaffected.** PyPI installation, README documentation links, and existing release tags continue to work. The only change visible externally is that issues and PRs against the public repo will be redirected to consult.
