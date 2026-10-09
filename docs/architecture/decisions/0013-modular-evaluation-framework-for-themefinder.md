# 13. Modular Evaluation Framework for Themefinder

Date: 2026-08-26

## Status

Accepted

Detailed design: [Modular Evaluation Framework for Themefinder](../design/modular-evaluation-framework.md).

## Context

`themefinder/evals/` already has a working LLM-quality evaluation framework: LLM-judge evaluators, dataset
loading, Langfuse tracing, a multi-model benchmark runner, and synthetic data generation. But the execution
engine and the artefact store are hard-wired together. There are four separate eval scripts for each component which each define their own set up for Langfuse or local running, and duplicate the majority of the logic across both paths. Mapping is the
one component where the two paths don't even share scoring logic. As a direct consequence, `langfuse` is a core, non-optional
dependency of the package purely to support the duplication, maintenance is a headache, and adding new evaluators or components is a non-trivial task.

We want a framework that starts with pydantic-evals as the execution engine (owning case iteration,
concurrency, retries, reporting) and treats Langfuse purely as dataset and artefact storage rather than as
the orchestrator — with both sides genuinely swappable for other tools later, not just swappable in theory. The framework should be modular in design and allow for easy extension to new components, evaluators and metrics. We also want DVC driving reproducible eval runs, wrapping the same entry points every other caller uses rather than becoming a fifth place the Langfuse-vs-local branching logic could fork.

## Decision

We are introducing a ports-and-adapters layer inside `themefinder/evals/` and migrating the four component
behaviours behind one reusable API and CLI, incrementally:

- Four ports — `DatasetPort`, `EvaluatorPort`, `RunnerPort`, `ArtefactStorePort` — each defined as an
  explicit `abc.ABC` base class (not structural typing), so adapters must genuinely subclass the interface
  they implement.
- One folder per port under `evals/adapters/` (`datasets/`, `evaluators/`, `runners/`, `artefact_stores/`),
  each holding its `base.py` plus one file per concrete implementation (e.g. `langfuse_adapter.py`,
  `local_json_adapter.py`).
- pydantic-evals becomes the default engine behind `RunnerPort`, selected via one env var
  (`THEMEFINDER_EVAL_ENGINE`) — the explicit seam a second engine plugs into later.
- `EvaluatorPort` is implemented directly by each kind of framework evaluator, not through a generic wrapper:
  the custom LLM-judge/metric adapters, plus a
  `PydanticEvalsEvaluator` (wrapping any native pydantic-evals evaluator, e.g. `LLMJudge`), built and
  unit-tested but not yet wired into any component — the landing spot for the team's expected future migration
  of the custom judges onto pydantic-evals' own judge primitive, per ADR-0011. `RunnerPort` implementations stay
  agnostic to which kind of evaluator they're invoking. `RunReport` also gains an optional `engine_report`
  field so `PydanticEvalsRunner`'s native `EvaluationReport` can reach `LangfuseArtefactStore` for a richer
  summary, without widening any port's real contract or requiring other adapters to know about it.
- Langfuse-specific code is confined to the Langfuse adapters and to `evals/config.py::resolve_backends()`,
  the single function that constructs the Langfuse context and passes its ownership to the artefact adapter.
  Component definitions and the unified API/CLI contain no Langfuse-specific code. `benchmark.py` still
  constructs its own Langfuse context and passes it through the generic `context` parameter.
- `resolve_backends()` selects the dataset source and the artefact store independently, not as one bundled
  "Langfuse configured" decision. Each defaults to local storage and can be explicitly set to Langfuse, so a
  run can pull cases from Langfuse while storing results locally, or the reverse. This
  check is answered from settings directly, without needing to construct a Langfuse context first — a fully
  local run never touches `langfuse_utils` at all. A dataset that's missing or inaccessible in Langfuse is a
  hard failure, not a silent fall back to a local fixture.
- Framework evaluators live in `evals/adapters/evaluators/`, one `EvaluatorPort` subclass per file.
  The legacy `evaluators.py` and `metrics.py` modules remain for callers outside the unified component path,
  including the existing mapping DVC prototype. `langfuse_utils.py` (plus the unrelated `utils.py`) separately
  becomes `evals/utils/`, one file per concern.
- `benchmark.py` uses the unified API for component execution but retains its existing Langfuse tracing and
  cost collection. `generate_synthetic.py` remains out of scope.
- `THEMEFINDER_EVAL_ENGINE` stays an env var, not a config file — consistent with the rest of `evals/`, which
  has no config-file infrastructure. But the scattered ad hoc `os.getenv()` calls that read those env vars
   are centralised into one `evals/settings.py::EvalSettings`, built once per process and injected
  as an optional parameter at the same points `context` already is. This is fixed in this pass, not deferred
  — scoped strictly to `themefinder/evals/` after confirming `backend/` already has proper Django settings
  and `lambda/`/`pipeline-*/` are independently-deployed units where per-file reads are appropriate.
- Every supported component run — direct CLI (`python run_eval.py --component ...`), `benchmark.py`, the
  `themefinder-eval.yml` CI workflow, and the future top-level DVC pipeline — converges on
  `evaluate_component(...)`, which is the only public entry point that calls
  `resolve_backends()`/`run_component()`.
- The set of eval component names has a single source of truth, rather than the former independent lists
  (`VALID_COMPONENTS`, `EVAL_FUNCS`, the CI workflow's `choices`, and future `evals/params.yaml`) kept in sync
  by hand — every other list
  either derives from it or is validated against it, so registering a new component is a one-place change. The
  shared `COMPONENT_NAMES` tuple is derived from the registry keys and used by datasets, benchmark, and the
  CLI, with a test keeping the CI workflow choices aligned. The future DVC parameters must use or be validated
  against it too.
- `evals/dvc.yaml` defines one pipeline stage per eval component (via DVC's `foreach`, driven by
  `evals/params.yaml`), each shelling out to the same `run_eval.py --component <name>` entry point every other
  caller uses.
  This buys `dvc repro`'s dependency-aware caching (skip a component entirely when nothing it depends on —
  dataset, evaluator code, the pipeline itself — has changed, via DVC's own hash tracking, unrelated to which
  artefact store is configured) and `dvc exp run`/`dvc metrics show` for comparing intentional variations as
  tracked experiments — not strict reproducibility, since LLM evals are stochastic, but a real win for
  "nothing relevant changed, don't bother re-running." The DVC implementation will make the unified CLI write
  its already-computed result to a stable local path
  (`evals/local_eval_runs/<component>/<dataset>/results.json`) regardless of which `ArtefactStorePort` was
  configured for that run — a concrete `metrics` file DVC can track whether the "official" record went to
  Langfuse or local JSON.

## Consequences

- The Langfuse package moves from a core dependency to an optional `eval` extra, alongside `scikit-learn`,
  `sentence-transformers`, and now `dvc`. This may not be a permanent change though if we use Langfuse for
  observability of production code.
- `evals/params.yaml` will introduce another representation of the component names, kept in sync via the
  single-source-of-truth decision above rather than maintained independently. `dvc init`'s exact location
  (repo root vs. a `themefinder/`
  subdirectory) and remote storage for `dvc push`/`dvc pull` are setup decisions not resolved by this ADR.
- Mapping uses one `MappingMetricsEvaluator` for both dataset sources. It delegates to the existing
  `metrics.py::calculate_mapping_metrics`, preserving F1, exact-match accuracy, overlap rate, and the F1
  confidence interval while removing the old local-versus-Langfuse execution split.
- The abstraction is proven rather than assumed: a swappability test runs the same cases through both
  `PydanticEvalsRunner` and a pydantic-evals-free inline runner and asserts identical output.
- More files and more indirection than the previous flat layout, but each port is independently testable
  offline, and Langfuse can be replaced (dataset storage, artefact storage, or both) without touching the
  component definitions, evaluators, or runner.
- `benchmark.py` and `generate_synthetic.py` still couple to Langfuse directly for now — the
  `evals/synthetic/` package itself has no Langfuse references, only its CLI wrapper does; migrating both
  onto the new ports is deferred to a follow-up pass. For `benchmark.py`, the minimal changes this would
  take — routing its context construction, flush, and cost/token metrics extraction through
  `resolve_backends`/`ArtefactStorePort` instead of calling `langfuse_utils` directly — are already scoped
  in the design doc, ready to pick up. `generate_synthetic.py` needs the equivalent de-Langfusing (its own
  `LangfuseContext` construction, trace wrap, and flush), tracked as a separate follow-up issue.
- Note (2026-09-24): to support a mix of evaluator sources (pydantic-evals, DeepEval, custom), `EvaluatorPort`
  stays the canonical hub — sources adapt in, runners adapt out — rather than adopting `pydantic_evals.Evaluator`
  as the base, which would privilege one library's context model and force `sources × runners` adapters instead
  of `sources + runners`. The cost is a reverse adapter (`EvaluatorPort → pydantic_evals.Evaluator`) plus
  `isinstance` dispatch for `PydanticEvalsEvaluator` on the native runner, which passes the engine's real
  context through `evaluate_in_context` so the adapter's error handling still applies.
