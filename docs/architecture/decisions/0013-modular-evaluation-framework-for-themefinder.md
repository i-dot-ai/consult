# 13. Modular Evaluation Framework for Themefinder

Date: 2026-08-19

## Status

Accepted

## Context

`themefinder/evals/` already has a working LLM-quality evaluation framework: LLM-judge evaluators, dataset
loading, Langfuse tracing, a multi-model benchmark runner, and synthetic data generation. But the execution
engine and the artefact store are hard-wired together. Each of the four stage eval scripts
(`eval_generation.py`, `eval_mapping.py`, `eval_condensation.py`, `eval_refinement.py`) hand-rolls its own
Langfuse-path/local-fallback branch, duplicating the majority of its logic across both paths, and the two
paths don't even share the same scoring logic — the Langfuse path uses the full LLM-judge suite, the local
fallback uses cheaper stats. As a direct consequence, `langfuse` is a core, non-optional dependency of the
package purely to support this duplication.

We want a framework that starts with pydantic-evals as the execution engine (owning case iteration,
concurrency, retries, reporting) and treats Langfuse purely as dataset and artefact storage rather than as
the orchestrator — with both sides genuinely swappable for other tools later, not just swappable in theory.

## Decision

We are introducing a ports-and-adapters layer inside `themefinder/evals/` and migrating the four stage
scripts onto it in place, incrementally:

- Four ports — `DatasetPort`, `EvaluatorPort`, `EvalRunnerPort`, `ArtefactStorePort` — each defined as an
  explicit `abc.ABC` base class (not structural typing), so adapters must genuinely subclass the interface
  they implement.
- One folder per port under `evals/adapters/` (`datasets/`, `evaluators/`, `runners/`, `artefact_stores/`),
  each holding its `base.py` plus one file per concrete implementation (e.g. `langfuse_adapter.py`,
  `local_json_adapter.py`).
- pydantic-evals becomes the default engine behind `EvalRunnerPort`, selected via one env var
  (`THEMEFINDER_EVAL_ENGINE`) — the explicit seam a second engine plugs into later.
- Langfuse-specific code is confined to the Langfuse adapters and to `evals/config.py::resolve_backends()`,
  the single function that constructs and owns the Langfuse context. The four stage scripts contain zero
  Langfuse-specific code — no import, no type reference, no branding in a parameter name. This required one
  mechanical change to `benchmark.py`'s call site (renaming its `langfuse_ctx` kwarg to a generic
  `context`), since `benchmark.py` is what constructs and passes the real Langfuse context through.
- For consistency, the same "one folder, one thing per file" convention is applied to two existing flat
  files: `evaluators.py` becomes `evals/evaluators/`, one evaluator per file, and `langfuse_utils.py` (plus
  the unrelated `utils.py`) become `evals/utils/`.
- `benchmark.py` (multi-model runner) and `evals/synthetic/` (synthetic data generation) are explicitly out
  of scope for this pass and keep working unchanged against the new stage-script signatures; adapting them
  to call the ports directly is deferred to a later pass.
- `THEMEFINDER_EVAL_ENGINE` stays an env var, not a config file. `evals/` already reads a dozen env vars via
  ad hoc `os.getenv()` calls scattered across `benchmark.py`, `langfuse_utils.py`, and `utils_gateway.py`,
  with no config-file infrastructure anywhere in the package — adding a file-based config format for one
  switch would be inconsistent with the codebase and adds parsing overhead for no benefit at this scale.

## Consequences

- `langfuse` moves from a core dependency to an optional `eval` extra, alongside `scikit-learn` and
  `sentence-transformers`.
- Local (no-Langfuse) runs now use the same LLM-judge evaluator suite as Langfuse runs, rather than the
  cheaper local-fallback stats — a disclosed behaviour change that removes an existing inconsistency between
  the two paths. `evals/metrics.py`, which powered the old fallback, becomes unused and is flagged as a
  follow-up deletion candidate.
- The abstraction is proven rather than assumed: a swappability test runs the same cases through both
  `PydanticEvalsRunner` and a pydantic-evals-free inline runner and asserts identical output.
- More files and more indirection than the current flat layout, but each port is independently testable
  offline, and Langfuse can be replaced (dataset storage, artefact storage, or both) without touching the
  eval scripts, the evaluators, or the runner.
- `benchmark.py` and `evals/synthetic/` still couple to Langfuse directly for now; migrating them onto the
  new ports is deferred to a follow-up pass, as is the `evals/metrics.py` removal and consolidating the
  scattered `os.getenv()` calls into one settings object.
