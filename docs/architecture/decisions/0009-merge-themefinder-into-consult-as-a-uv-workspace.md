# 9. Merge themefinder into consult as a uv workspace

Date: 2026-05-01

## Status

Accepted

## Context

ThemeFinder lives in a separate public repository ([i-dot-ai/themefinder](https://github.com/i-dot-ai/themefinder)) and is consumed by consult as a PyPI dependency. In practice, consult is themefinder's only real consumer: the backend and both pipeline scripts (`pipeline-sign-off`, `pipeline-mapping`) import its internals directly.

The two-repo split forces a heavy release dance for any change that spans both projects (edit themefinder → cut a PyPI release → bump pins in consult → rebuild four Docker images), which biases against making themefinder changes in tandem with consult work. It also leaves room for version drift: each Docker image resolves themefinder independently at build time rather than from a shared lock.

ThemeFinder is still useful to publish to PyPI for external users (other government teams, researchers). Any restructuring needs to preserve PyPI publishability and keep release tags discoverable.

## Decision

We will move themefinder into consult as a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) member, alongside the backend and the two pipelines.

1. **Single workspace, four packages.** `consult/` becomes a uv workspace whose members are `backend/`, `themefinder/`, `pipeline-sign-off/`, and `pipeline-mapping/`. A single root `pyproject.toml` declares the workspace; a single root `uv.lock` resolves dependencies for all four members together.
2. **ThemeFinder stays publishable.** Its `pyproject.toml` is preserved unchanged so `pip install themefinder` continues to work for external users. Internal consumers reference it through `[tool.uv.sources] themefinder = { workspace = true }`, which uv installs editable.
3. **Pipelines become workspace members.** Today both pipelines pull their dependency set transitively through `themefinder>=0.8.2`. After migration, each pipeline's `pyproject.toml` lists its dependencies explicitly, and its Dockerfile is rewritten as a multi-stage uv build mirroring `backend/Dockerfile`.
4. **PyPI publishing moves into consult; the public repo is archived.** ThemeFinder continues to be published to PyPI, but from consult: a release workflow here builds and publishes the `themefinder/` package on a version bump. The public `i-dot-ai/themefinder` repo is archived (made read-only) with a redirect notice in its README pointing users to consult for source, issues, and releases. Existing PyPI release tags on the public repo remain valid; new releases are cut from consult.

### Source provenance

The `themefinder/` directory is a verbatim, like-for-like copy of the upstream repo at the point of import. Recording the exact source commit here (rather than only in the migration PR) so it isn't lost and future divergence in this monorepo can be diffed back against upstream.

- **Upstream repo:** [i-dot-ai/themefinder](https://github.com/i-dot-ai/themefinder)
- **Copied from commit:** [`09918eb213e0`](https://github.com/i-dot-ai/themefinder/commit/09918eb213e0) — *"Merge pull request #136 from i-dot-ai/fix/strip-response-text-whitespace"* (tip of `main`, 2026-05-07)
- **Declared version:** `0.8.2` (`themefinder/pyproject.toml`)

Note: the import was taken from the tip of upstream `main` (`09918eb2`), which is a few commits *ahead* of the [`v0.8.2` release tag](https://github.com/i-dot-ai/themefinder/releases/tag/v0.8.2) (`dcb92a1f`) — they are **not** identical (e.g. `src/themefinder/models.py` differs). Every file under `themefinder/src/` and `themefinder/tests/` was verified to match `09918eb2` byte-for-byte at import. Excluded from the copy: `.git`, `.github`, build artefacts, and themefinder's own `uv.lock`.

To re-verify or diff the in-repo copy against upstream later:

```bash
git clone https://github.com/i-dot-ai/themefinder /tmp/tf && git -C /tmp/tf checkout 09918eb213e0
diff -r themefinder/src /tmp/tf/src
diff -r themefinder/tests /tmp/tf/tests
```

### Alternatives considered

- **Git submodule pointing at the themefinder repo.** Rejected: submodules require every consumer (and CI) to run `git submodule update`, keep themefinder pinned to a commit in a separate repo rather than editable alongside consult, and don't compose with a uv workspace or the single-root-`uv.lock` goal — the version drift we're trying to remove would persist.
- **Keep the pipelines on `pip install -r requirements.txt`.** Rejected: leaves two dependency-management tools coexisting in one monorepo and pipeline dependencies unlocked.
- **Git subtree import (preserving themefinder history inside consult).** Rejected: the histories don't share roots, the import would balloon consult's history, and PyPI release tags can stay attached to the public-repo commits regardless.
- **Keep the public repo as a live mirror via subtree-split sync.** Rejected: it requires a force-push workflow and a perpetually-rewritten public history to maintain, for little benefit once consult is the source of truth and PyPI serves external users directly. Archiving with a redirect notice is simpler and the source remains readable.

## Consequences

### Positive

- **Single-PR cross-cutting changes.** Edits that span themefinder and consult become one review, one merge, one deploy.
- **No silent version drift.** A single root `uv.lock` guarantees backend and both pipelines run identical themefinder code.
- **Faster local dev loop.** Workspace members install editable, so a change in `themefinder/src/` is immediately visible to backend tests and pipeline scripts.
- **One CI surface to maintain.** ThemeFinder's tests, evals, and pre-commit move into consult, replacing three separately-evolved workflow sets.

### Negative

- **The migration PR is unavoidably large and atomic.** `build-gh.yml` builds four Docker images from repo-root context on every push, so the workspace wiring, all four Dockerfiles, the Makefile, and the CI workflows must land together.
- **Editable installs require runtime source.** uv writes a `.pth` file pointing at `themefinder/src/`, so all three Python images must copy `themefinder/src/` and `themefinder/pyproject.toml` into their **runtime** stage, not just the build stage.
- **External contributions reroute to consult.** The public repo becomes archived/read-only, so issues and PRs can no longer be filed against the familiar `themefinder` repo and must go to consult instead.
- **PyPI release moves to consult.** A version bump to `themefinder/` merges to consult main, and a release workflow here publishes to PyPI directly — no separate release in the public repo.

### Neutral

- **External users are largely unaffected.** PyPI installs and existing release tags continue to work. The archived public repo stays readable with a redirect notice; new issues and PRs go to consult.
