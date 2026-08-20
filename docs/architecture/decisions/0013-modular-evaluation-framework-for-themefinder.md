# 13. Modular Evaluation Framework for Themefinder

Date: 2026-08-19

## Status

Accepted

Detailed design: [Modular Evaluation Framework for Themefinder](../design/modular-evaluation-framework.md).

## Context

`themefinder/evals/` already has a working LLM-quality evaluation framework: LLM-judge evaluators, dataset
loading, Langfuse tracing, a multi-model benchmark runner, and synthetic data generation. But the execution
engine and the artefact store are hard-wired together. Each of the four stage eval scripts
(`eval_generation.py`, `eval_mapping.py`, `eval_condensation.py`, `eval_refinement.py`) hand-rolls its own
Langfuse-path/local-fallback branch, duplicating the majority of its logic across both paths. Mapping is the
one stage where the two paths don't even share scoring logic — its Langfuse path uses `evaluators.py`'s
LLM-judge-free F1 evaluator, its local fallback uses a separate sklearn-based implementation in `metrics.py`;
generation, condensation, and refinement are already consistent, each calling the same `evaluators.py`
functions in both paths. As a direct consequence, `langfuse` is a core, non-optional dependency of the
package purely to support the duplication.

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
- `THEMEFINDER_EVAL_ENGINE` stays an env var, not a config file — consistent with the rest of `evals/`, which
  has no config-file infrastructure. But the scattered ad hoc `os.getenv()` calls that read those env vars
  (8 vars, 17 call sites across 9 files, with `AUTO_EVAL_4_1_SWEDEN_DEPLOYMENT` alone read independently in
  5 places) are centralised into one `evals/settings.py::EvalSettings`, built once per process and injected
  as an optional parameter at the same points `context` already is. This is fixed in this pass, not deferred
  — scoped strictly to `themefinder/evals/` after confirming `backend/` already has proper Django settings
  and `lambda/`/`pipeline-*/` are independently-deployed units where per-file reads are appropriate.
- Every way an eval gets run — direct CLI (`python eval_generation.py`), `benchmark.py`, and the
  `themefinder-eval.yml` CI workflow — is required to converge on the same `evaluate_X(...)` function per
  stage, which is the only thing allowed to call `resolve_backends`/`run_stage`. No caller gets its own copy
  of the Langfuse-vs-local branching logic ever again.

## Consequences

- `langfuse` moves from a core dependency to an optional `eval` extra, alongside `scikit-learn` and
  `sentence-transformers`.
- Mapping's local runs now use `evaluators.py::mapping_f1_evaluator` instead of the separate
  `metrics.py::calculate_mapping_metrics` implementation — a disclosed behaviour change that removes mapping's
  Langfuse-vs-local inconsistency, the only one remaining (generation, condensation, and refinement were
  already consistent). `evals/metrics.py`, which powered the old mapping fallback, is deleted outright in
  this pass once `eval_mapping.py`'s import of it is removed.
- The abstraction is proven rather than assumed: a swappability test runs the same cases through both
  `PydanticEvalsRunner` and a pydantic-evals-free inline runner and asserts identical output.
- More files and more indirection than the current flat layout, but each port is independently testable
  offline, and Langfuse can be replaced (dataset storage, artefact storage, or both) without touching the
  eval scripts, the evaluators, or the runner.
- `benchmark.py` and `evals/synthetic/` still couple to Langfuse directly for now; migrating them onto the
  new ports is deferred to a follow-up pass.
