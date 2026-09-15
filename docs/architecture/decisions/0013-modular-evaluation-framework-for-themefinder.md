# 13. Modular Evaluation Framework for Themefinder

Date: 2026-08-26

## Status

In Review

Detailed design: [Modular Evaluation Framework for Themefinder](../design/modular-evaluation-framework.md).

## Context

`themefinder/evals/` already has a working LLM-quality evaluation framework: LLM-judge evaluators, dataset
loading, Langfuse tracing, a multi-model benchmark runner, and synthetic data generation. But the execution
engine and the artefact store are hard-wired together. There are four separate eval scripts for each stage which each define their own set up for Langfuse or local running, and duplicate the majority of the logic across both paths. Mapping is the
one stage where the two paths don't even share scoring logic. As a direct consequence, `langfuse` is a core, non-optional
dependency of the package purely to support the duplication, maintenance is a headache, and adding new evaluators or stages is a non-trivial task.

We want a framework that starts with pydantic-evals as the execution engine (owning case iteration,
concurrency, retries, reporting) and treats Langfuse purely as dataset and artefact storage rather than as
the orchestrator — with both sides genuinely swappable for other tools later, not just swappable in theory. The framework should be modular in design and allow for easy extension to new stages, evaluators and metrics. We also want DVC driving reproducible eval runs, wrapping the same entry points every other caller uses rather than becoming a fifth place the Langfuse-vs-local branching logic could fork.

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
- `EvaluatorPort` is implemented directly by each kind of evaluator, not through a generic wrapper: the
  seven custom LLM-judge/metric classes retired from `evaluators.py`, plus a new
  `PydanticEvalsLLMJudgeAdapter` (wrapping pydantic-evals' native `LLMJudge`), built and unit-tested but not
  yet wired into any stage — the landing spot for the team's expected future migration of the custom
  judges onto pydantic-evals' own judge primitive, per ADR-0011. `EvalRunnerPort` implementations stay
  agnostic to which kind of evaluator they're invoking. `RunReport` also gains an optional `engine_report`
  field so `PydanticEvalsRunner`'s native `EvaluationReport` can reach `LangfuseArtefactStore` for a richer
  summary, without widening any port's real contract or requiring other adapters to know about it.
- Langfuse-specific code is confined to the Langfuse adapters and to `evals/config.py::resolve_backends()`,
  the single function that constructs and owns the Langfuse context. The four stage scripts contain zero
  Langfuse-specific code — no import, no type reference, no branding in a parameter name. This required one
  mechanical change to `benchmark.py`'s call site (renaming its `langfuse_ctx` kwarg to a generic
  `context`), since `benchmark.py` is what constructs and passes the real Langfuse context through.
- `resolve_backends()` selects the dataset source and the artefact store independently, not as one bundled
  "Langfuse configured" decision — each defaults to Langfuse when credentials are set but is separately
  overridable, so a run can pull cases from Langfuse while storing results locally, or the reverse. This
  check is answered from settings directly, without needing to construct a Langfuse context first — a fully
  local run never touches `langfuse_utils` at all. A dataset that's missing or inaccessible in Langfuse is a
  hard failure, not a silent fall back to a local fixture.
- `evaluators.py` retires directly into `evals/adapters/evaluators/`, one `EvaluatorPort` subclass per file
  — not a separate `evals/evaluators/` content package next to the port, which would be confusing to tell
  apart from the port itself. `langfuse_utils.py` (plus the unrelated `utils.py`) separately becomes
  `evals/utils/`, one file per concern.
- `benchmark.py` (multi-model runner) and `generate_synthetic.py` (synthetic data generation's CLI entry
  point — the only place in that call path with Langfuse references; the `evals/synthetic/` package it wraps
  has none) are explicitly out of scope for this pass and keep working unchanged against the new stage-script
  signatures with minimal changes required in benchmark.
- `THEMEFINDER_EVAL_ENGINE` stays an env var, not a config file — consistent with the rest of `evals/`, which
  has no config-file infrastructure. But the scattered ad hoc `os.getenv()` calls that read those env vars
   are centralised into one `evals/settings.py::EvalSettings`, built once per process and injected
  as an optional parameter at the same points `context` already is. This is fixed in this pass, not deferred
  — scoped strictly to `themefinder/evals/` after confirming `backend/` already has proper Django settings
  and `lambda/`/`pipeline-*/` are independently-deployed units where per-file reads are appropriate.
- Every way an eval gets run — direct CLI (`python eval_generation.py`), `benchmark.py`, the
  `themefinder-eval.yml` CI workflow, and now DVC (`dvc repro`/`dvc exp run` via `evals/dvc.yaml`) — is
  required to converge on the same `evaluate_X(...)` function per stage, which is the only thing allowed to
  call `resolve_backends`/`run_stage`. No caller gets its own copy of the Langfuse-vs-local branching logic
  ever again.
- The set of eval stage names has a single source of truth, not independent lists (`VALID_STAGES`,
  `EVAL_FUNCS`, the CI workflow's `choices`, `evals/params.yaml`) kept in sync by hand — every other list
  either derives from it or is validated against it, so registering a new stage is a one-place change. The
  exact mechanism (a shared constant the others read, a generation step, a test asserting the lists agree,
  or something else) is left to implementation time, designed and implemented as part of the DVC pipeline
  work (Wave 4), since `evals/params.yaml` is the fourth independent list and introducing it is the point
  the duplication is fixed rather than added to.
- `evals/dvc.yaml` defines one pipeline stage per eval stage (via DVC's `foreach`, driven by
  `evals/params.yaml`), each shelling out to the same `eval_<stage>.py` entry point every other caller uses.
  This buys `dvc repro`'s dependency-aware caching (skip a stage entirely when nothing it depends on —
  dataset, evaluator code, the pipeline itself — has changed, via DVC's own hash tracking, unrelated to which
  artefact store is configured) and `dvc exp run`/`dvc metrics show` for comparing intentional variations as
  tracked experiments — not strict reproducibility, since LLM evals are stochastic, but a real win for
  "nothing relevant changed, don't bother re-running." Each CLI entry point's `__main__` block writes its
  already-computed result to a stable local path
  (`evals/local_eval_runs/<stage>/<dataset>/results.json`) regardless of which `ArtefactStorePort` was
  configured for that run — a concrete `metrics` file DVC can track whether the "official" record went to
  Langfuse or local JSON.

## Consequences

- The Langfuse package moves from a core dependency to an optional `eval` extra, alongside `scikit-learn`,
  `sentence-transformers`, and now `dvc`. This may not be a permanent change though if we use Langfuse for
  observability of production code.
- `evals/params.yaml` becomes a fourth place that names eval stages, alongside `VALID_STAGES`, `EVAL_FUNCS`,
  and the CI workflow's `choices` — kept in sync via the single-source-of-truth decision above rather than
  left as four lists maintained by hand. `dvc init`'s exact location (repo root vs. a `themefinder/`
  subdirectory) and remote storage for `dvc push`/`dvc pull` are setup decisions not resolved by this ADR.
- Mapping's local runs now use `MappingF1Evaluator` instead of the separate
  `metrics.py::calculate_mapping_metrics` implementation — a disclosed behaviour change that removes mapping's
  Langfuse-vs-local inconsistency, the only one remaining (generation, condensation, and refinement were
  already consistent). `evals/metrics.py`, which powered the old mapping fallback, is deleted outright in
  this pass once `eval_mapping.py`'s import of it is removed.
- The abstraction is proven rather than assumed: a swappability test runs the same cases through both
  `PydanticEvalsRunner` and a pydantic-evals-free inline runner and asserts identical output.
- More files and more indirection than the current flat layout, but each port is independently testable
  offline, and Langfuse can be replaced (dataset storage, artefact storage, or both) without touching the
  eval scripts, the evaluators, or the runner.
- `benchmark.py` and `generate_synthetic.py` still couple to Langfuse directly for now — the
  `evals/synthetic/` package itself has no Langfuse references, only its CLI wrapper does; migrating both
  onto the new ports is deferred to a follow-up pass. For `benchmark.py`, the minimal changes this would
  take — routing its context construction, flush, and cost/token metrics extraction through
  `resolve_backends`/`ArtefactStorePort` instead of calling `langfuse_utils` directly — are already scoped
  in the design doc, ready to pick up. `generate_synthetic.py` needs the equivalent de-Langfusing (its own
  `LangfuseContext` construction, trace wrap, and flush), tracked as a separate follow-up issue.
