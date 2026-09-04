# 14. DVC for eval pipeline version control

Date: 2026-08-21

## Status

Accepted

## Context

ThemeFinder's evaluation suite (`themefinder/evals/`) is how we measure generation, condensation,
refinement, and mapping quality before and after model/prompt changes (see ADR-0011). Until now,
each stage has been orchestrated by ad-hoc Python: a script for data download, a script for
running the evaluation, and — for multi-model sweeps — `benchmark.py` calling those scripts in
turn.

This has two costly consequences:

- **No caching.** Every invocation re-runs every stage from scratch, regardless of whether the
  code, data, or parameters it depends on have actually changed. Evaluation stages call out to
  LLMs (including LLM-as-judge scoring), so a stage re-run is not free — it consumes real API
  spend and wall-clock time, even when nothing relevant has changed since the last run.
- **No dependency tracking between stages.** Parameters are scattered across CLI flags and
  environment variables rather than held in one place, and nothing enforces that a change to a
  shared file (a prompt, an evaluator, an upstream dataset) causes every downstream stage that
  depends on it to be re-run. It is left to whoever made the change to remember which scripts to
  re-trigger, and in which order — with the risk that a stale downstream result is mistaken for a
  current one.

We need an orchestration layer that treats the eval pipeline as a versioned, reproducible DAG:
one that only re-runs what has actually changed, but *guarantees* that anything downstream of a
change is re-run, not skipped.

## Decision

We will use [DVC](https://dvc.org/) (Data Version Control) to define and run the ThemeFinder eval
pipelines, starting with the theme mapping component.

- Each pipeline component gets its own directory under `themefinder/evals/pipelines/<component>/`
  (starting with `mapping/`), containing:
  - `dvc.yaml` — declares the pipeline's stages (e.g. `download_data`, `evaluate`), and for each
    stage its `deps` (code files, shared modules, upstream data directories) and `outs`
    (downloaded data, result files).
  - `params.yaml` — the single, version-controlled source of parameters for that pipeline (e.g.
    `dataset`, `model`), replacing scattered CLI flags and env vars.
- Stages are run via `dvc repro` (`uv run --package themefinder --extra dev dvc repro`), which
  hashes each stage's declared `deps` and `params`, compares them against the last successful run
  recorded in `dvc.lock`, and:
  - **skips** a stage if nothing in its `deps`/`params` has changed since it last ran
    successfully, reusing the cached output, or
  - **re-runs** a stage — and every stage downstream of it in the DAG — if anything it depends on
    has changed.
- Pin `dvc>=3.55` to benefit from its features for experiment management
- Data will be version-controlled by establishing an S3 bucket as a DVC remote. This bucket will
  mirror the contents of LangFuse, which is the single source of truth for data.
- Component-specific pipelines will be implemented through separate PRs, starting with the `mapping`
  component

## Consequences

### Positive

- **Lower eval running costs.** LLM calls (task model and judge model) are the dominant cost of
  running evals. Because `dvc repro` only re-executes stages whose dependencies have actually
  changed, unrelated or unchanged stages are skipped entirely on every re-run — directly cutting
  the number of billed LLM calls compared to the previous "always run everything" scripts,
  especially for contributors iterating locally or for CI runs on PRs that only touch one
  pipeline stage.
- **No missed re-runs.** Because dependencies are declared explicitly in `dvc.yaml`, a change to
  any shared file (a prompt, an evaluator, a metrics helper, or an upstream dataset) automatically
  marks every downstream stage that consumes it as stale, and `dvc repro` re-runs all of them. This
  removes the previous risk of a human forgetting which scripts to re-trigger after a shared-code
  change, and closes the gap where a downstream result could silently go stale relative to its
  inputs.
- **Reproducibility and auditability.** `dvc.lock` records the exact hash of every stage's
  `deps`/`params`/`outs` at the time it last ran, so any historical eval result can be tied back
  to the precise code, data, and parameter state that produced it.
- **Centralised, diffable parameters.** `params.yaml` replaces parameters previously scattered
  across CLI flags and env vars, making parameter changes visible and reviewable in PRs.
- **Foundation for numeric comparison.** This sets up future use of `dvc metrics show` / `dvc
  metrics diff` to compare model or prompt changes numerically across commits, rather than reading
  through ad-hoc console output.

### Negative

- **New tool for contributors to learn**, plus a `.dvc` control directory and local cache per
  pipeline to be aware of (though usage is limited to `dvc repro`/`dvc dag` for now).
- **Two orchestration mechanisms coexist temporarily.** Only the mapping pipeline runs through DVC
  today; generation, condensation, and refinement still run through the older ad-hoc scripts until
  they are migrated in follow-up work.

## Related

- `docs/architecture/decisions/0009-merge-themefinder-into-consult-as-a-uv-workspace.md`
- `docs/architecture/decisions/0011-evaluation-tooling.md`
