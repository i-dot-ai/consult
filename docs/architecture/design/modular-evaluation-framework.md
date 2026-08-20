# Modular Evaluation Framework for Themefinder

This is the detailed design behind [ADR-0013](../decisions/0013-modular-evaluation-framework-for-themefinder.md). The ADR
records the decision and its consequences; this document is the reference for how the framework is actually
built — directory layout, types, interfaces, and the rules that keep it swappable in practice, not just in
theory.

Everything here lives under `themefinder/evals/`.

## Problem

`themefinder/evals/` has a working LLM-quality evaluation framework: LLM-judge evaluators, dataset loading,
Langfuse tracing, a multi-model benchmark runner, synthetic data generation. But the execution engine and the
artefact store are hard-wired together. Each of the four stage eval scripts —
`eval_generation.py`, `eval_mapping.py`, `eval_condensation.py`, `eval_refinement.py` — hand-rolls its own
`_run_with_langfuse(...)` / `_run_local_fallback(...)` branch, duplicating most of its logic across both
paths. Mapping is the one stage where the two paths don't even share scoring logic: its Langfuse path calls
`evaluators.py::mapping_f1_evaluator`, its local fallback calls a separate sklearn-based implementation,
`metrics.py::calculate_mapping_metrics`. Generation, condensation, and refinement are already consistent —
each already calls the same `evaluators.py` LLM-judge functions in both paths. As a direct result, `langfuse`
is a core, non-optional dependency of the package purely to support the duplication.

## Goals

- pydantic-evals is the execution engine: it owns case iteration, concurrency, retries, and reporting.
- Langfuse is dataset + artefact storage only — not the orchestrator.
- Both the engine and the storage backend are genuinely swappable, proven by a test, not just structurally
  possible.
- Zero Langfuse-specific code in the four stage scripts: no import, no type reference, no branding in a
  parameter name.
- Migrate in place, incrementally, with each phase independently revertible.

## Non-goals (this pass)

- `benchmark.py` (multi-model runner) keeps calling the four stage functions exactly as it does today, with
  one single-line exception (see [Compatibility contract](#compatibility-contract-with-benchmarkpy)). It is
  not rewritten to call the new ports directly.
- `evals/synthetic/` (synthetic data generation) is untouched.

## One entry point per stage, shared by every caller

Every way an eval actually gets run converges on the same function call:

```
python eval_generation.py --dataset X        ─┐
benchmark.py --evals generation / --quick      ├──▶  evaluate_generation(dataset, llm, judge_llm, context)
themefinder-eval.yml (CI, workflow_dispatch)  ─┘            │
                                                             ▼
                                              resolve_backends(context, stage, dataset) ──▶ run_stage(...)
```

`eval_generation.py`'s `__main__` block calls `asyncio.run(evaluate_generation(dataset=args.dataset))` — the
same function `benchmark.py::EVAL_FUNCS["generation"]` points at, which the `themefinder-eval.yml` workflow
also reaches (via `benchmark.py --evals "$EVAL_TYPE"` or `--quick`). No caller has its own copy of the
Langfuse-vs-local branching logic. This is the property that makes the framework's swappability real for
every caller, not just for tests: **every `eval_*.py`'s `__main__`/CLI block calls its own module's
`evaluate_X` wrapper, never a lower-level function like `run_stage` directly** — so a CLI run and a
`benchmark.py` run of the same stage are guaranteed to take the identical path through `resolve_backends` and
`run_stage`.

### Adding a new eval stage

The pattern to extend the framework to a new stage, rather than hand-rolling a one-off script that bypasses
the ports:

1. Add the stage name to `datasets.py::VALID_STAGES`.
2. Add local fixture data under `evals/data/<dataset>/` for the new stage.
3. Write the evaluator(s) as a new file in `evals/evaluators/`, exported from `evals/evaluators/__init__.py`.
4. Write `evals/eval_<stage>.py`: a `_task(inputs, llm)` function, a module-level `StageConfig`, and a thin
   `evaluate_<stage>(dataset, llm, judge_llm, context)` wrapper calling `resolve_backends` + `run_stage` —
   copy the shape of `eval_generation.py`.
5. Register it in `benchmark.py::EVAL_FUNCS` (and its `evals_with_judge` set, if the stage uses an LLM
   judge).
6. Add the stage to `.github/workflows/themefinder-eval.yml`'s `eval_type` `choices` list.

Steps 1, 5, and 6 are three independent lists of the same stage names — `VALID_STAGES`, `EVAL_FUNCS`, and the
workflow YAML — with nothing deriving one from another. All three must be updated by hand; missing one means
a stage silently works in some entry points and not others (most commonly: it works locally and via
`benchmark.py`, but never appears in the CI dropdown).

## Architecture overview

Four ports, each an explicit `abc.ABC`, each with a default adapter:

| Port | Role | Default adapter |
|---|---|---|
| `DatasetPort` | Load `list[Case]` for a stage/dataset | `LangfuseDatasetAdapter`, composed with `LocalJSONDatasetAdapter` via `FallbackDatasetAdapter` |
| `EvaluatorPort` | Score a case's output | `CallableEvaluatorAdapter`, wrapping the LLM-judge functions in `evals/evaluators/` |
| `EvalRunnerPort` | Orchestrate task execution + evaluation | `PydanticEvalsRunner`, wrapping `pydantic_evals.Dataset.evaluate` |
| `ArtefactStorePort` | Persist run/case results and scores | `LangfuseArtefactStore` (default), `LocalJSONArtefactStore` (no-Langfuse) |

```
eval_generation.py ─┐   evaluate_generation(dataset, llm, context, judge_llm):
eval_mapping.py     ─┤     backends = resolve_backends(context, stage=STAGE.stage, dataset=dataset)
eval_condensation.py│      return await run_stage(STAGE, dataset, backends, llm, judge_llm)
eval_refinement.py ─┘
        config.py::resolve_backends(context, stage, dataset) → EvalBackends(dataset, artefacts, runner, context_owned)
                                                                 (the only place that touches langfuse_utils / LangfuseContext)
        stage_runner.py::run_stage(stage, dataset, backends, llm, judge_llm) — pure ports, no Langfuse import:
          backends.dataset.load_cases(config)          → list[Case]
          StageConfig.build_evaluators(judge_llm)       → list[EvaluatorPort]   (wraps evals/evaluators/, unchanged)
          backends.runner.run(cases, task, evaluators)  → RunReport             (pydantic-evals today)
          backends.artefacts.record_case / finish_run   → flat dict             (Langfuse scores or local JSON;
                                                                                    LangfuseArtefactStore flushes in
                                                                                    finish_run() iff context_owned)
```

`context` is deliberately untyped (`Any`) at every boundary the stage scripts touch. They forward it to
`resolve_backends` without inspecting it — they have no idea what it is, Langfuse-shaped or otherwise.

## Directory structure

One folder per port, each holding an explicit `abc.ABC` base class in `base.py` and one concrete adapter per
file:

```
evals/adapters/
  __init__.py
  datasets/
    __init__.py
    base.py                  # DatasetPort(ABC) — load_cases(config) -> list[Case]
    langfuse_adapter.py        # LangfuseDatasetAdapter
    local_json_adapter.py       # LocalJSONDatasetAdapter
    fallback_adapter.py          # FallbackDatasetAdapter (tries primary, falls back to secondary; logs on fallback)
  evaluators/
    __init__.py
    base.py                  # EvaluatorPort(ABC) — async evaluate(case, output) -> list[Score]
    llm_judge_adapter.py        # CallableEvaluatorAdapter, wraps evals/evaluators/ factories unchanged
    pydantic_evals_llm_judge_adapter.py  # PydanticEvalsLLMJudgeAdapter, wraps pydantic_evals.evaluators.LLMJudge
                                            # (built + tested, not wired into any StageConfig yet)
  runners/
    __init__.py
    base.py                  # EvalRunnerPort(ABC) — async run(cases, task, evaluators, max_concurrency) -> RunReport
    pydantic_evals_adapter.py   # PydanticEvalsRunner, wraps pydantic_evals.Dataset.evaluate
  artefact_stores/
    __init__.py
    base.py                  # ArtefactStorePort(ABC) — start_run/record_case/finish_run
    langfuse_adapter.py        # LangfuseArtefactStore
    local_json_adapter.py       # LocalJSONArtefactStore
```

No adapter file imports from a sibling adapter file — each implementation depends only on its own `base.py`.
Filenames use an explicit `_adapter.py` suffix (rather than e.g. `langfuse.py`) so nothing in this tree
shadows the real third-party `langfuse` / `pydantic_evals` packages by name.

`eval_types.py` (shared domain dataclasses), `stage_runner.py`, and `config.py` are orchestration, not
themselves adapters, and stay at the top level of `evals/`.

### Two more flat files, split the same way

Applying the same "one folder, one thing per file" convention beyond the new adapter code:

**`evals/evaluators/`** replaces the flat `evals/evaluators.py`. Not to be confused with
`evals/adapters/evaluators/` (the port + the one generic adapter that wraps whatever lives here) —
`evals/evaluators/` holds the actual LLM-judge scoring implementations that adapter wraps:

```
evals/evaluators/
  __init__.py                  # re-exports the seven public evaluator callables, so llm_judge_adapter.py
                                # imports `from evaluators import ...` exactly as eval_*.py did from the
                                # flat module today — only the internal layout changed
  common.py                    # shared helpers used by 2+ evaluators: _parse_json_markdown,
                                # _make_evaluation, _shuffle_themes, _parse_evaluation_response, _build_comment
  groundedness.py               # create_groundedness_evaluator + _calculate_groundedness_scores
  coverage.py                    # create_coverage_evaluator + _calculate_coverage_scores
  mapping_f1.py                   # mapping_f1_evaluator
  title_specificity.py             # create_title_specificity_evaluator + _calculate_title_specificity
  condensation_quality.py           # create_condensation_quality_evaluator + _calculate_condensation_scores
  refinement_quality.py              # create_refinement_quality_evaluator + _calculate_refinement_scores
  redundancy.py                       # create_redundancy_evaluator + _get_sentence_model + calculate_redundancy_score
```

Grounded in the actual current contents of `evaluators.py`: seven public evaluators plus five shared private
helpers. Each file imports only `common.py` plus its own stage-specific dependencies — no evaluator file
imports another evaluator file. Function bodies move verbatim; nothing is rewritten in the split.

**`evals/utils/`** replaces the flat `evals/langfuse_utils.py` and the unrelated `evals/utils.py`:

```
evals/utils/
  __init__.py
  langfuse_utils.py             # moved verbatim — same public functions (get_langfuse_context, trace_context,
                                 # flush, extract_session_metrics, ...)
  prompt_utils.py                # moved verbatim from evals/utils.py (read_and_render) — renamed only
                                  # because a `utils.py` module and a `utils/` package can't coexist at the
                                  # same directory level; nothing in evals/ imports read_and_render today
```

Every `import langfuse_utils` site becomes `from utils import langfuse_utils`; call sites like
`langfuse_utils.get_langfuse_context(...)` are unchanged. `benchmark.py` and `generate_synthetic.py` keep
this import long-term — they legitimately talk to Langfuse. The four `eval_*.py` stage scripts have their
`import langfuse_utils` line deleted entirely, not relocated.

## Domain types — `evals/eval_types.py`

Framework-owned types, so no port implementation needs to import `pydantic_evals` or `langfuse` types
directly:

```python
@dataclass(frozen=True)
class Case:
    id: str
    inputs: dict[str, Any]
    expected_output: dict[str, Any] | None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Score:
    name: str
    value: float
    comment: str = ""

@dataclass
class CaseOutcome:
    case: Case
    output: Any
    scores: list[Score]
    error: str | None = None

@dataclass
class RunReport:
    outcomes: list[CaseOutcome]
    engine_report: Any | None = None   # opaque escape hatch for a runner's own native report
                                        # object (e.g. pydantic_evals.reporting.EvaluationReport).
                                        # None for runners without one. Untyped deliberately —
                                        # eval_types.py never imports pydantic_evals.

@dataclass
class StageConfig:
    stage: str                                              # one of datasets.VALID_STAGES
    task: Callable[[dict, Any], Awaitable[dict]]             # (case.inputs, llm) -> output dict
    build_evaluators: Callable[[Any], list["EvaluatorPort"]] # (judge_llm) -> evaluators
    case_filter: Callable[[Case], bool] | None = None

class DatasetNotFoundError(Exception): ...
```

`Score` is isomorphic to today's `{"name", "value", "comment"}` shape, so converting `evaluators.py` output
is a one-liner.

`StageConfig.task` takes `case.inputs` — a plain `dict` — not the full `Case` object. This is deliberate: it
matches pydantic-evals' native task contract exactly (`Dataset.evaluate(task)` invokes `task` with just the
case's `inputs`), so `PydanticEvalsRunner` needs no bridging on the task side. `run_stage` binds `llm` once
via `functools.partial(stage.task, llm=llm)` before handing the resulting `Callable[[dict], Awaitable[dict]]`
to whichever runner is active. If a stage genuinely needs data from `Case.metadata` inside its task, that
data is folded into `inputs` when the dataset adapter builds the `Case`, rather than widening this signature
back to the full `Case`.

## Ports

```python
# evals/adapters/datasets/base.py
class DatasetPort(abc.ABC):
    @abc.abstractmethod
    def load_cases(self, config: DatasetConfig) -> list[Case]: ...

# evals/adapters/evaluators/base.py
class EvaluatorPort(abc.ABC):
    @abc.abstractmethod
    async def evaluate(self, case: Case, output: Any) -> list[Score]: ...

# evals/adapters/runners/base.py
class EvalRunnerPort(abc.ABC):
    @abc.abstractmethod
    async def run(self, cases, task, evaluators, *, max_concurrency: int = 4) -> RunReport: ...

# evals/adapters/artefact_stores/base.py
class ArtefactStorePort(abc.ABC):
    @abc.abstractmethod
    def start_run(self, stage: str, dataset: str, metadata: dict) -> Any: ...
    @abc.abstractmethod
    def record_case(self, run_handle: Any, outcome: CaseOutcome) -> None: ...
    @abc.abstractmethod
    def finish_run(self, run_handle: Any, *, engine_report: Any | None = None) -> dict: ...
```

Every concrete adapter — `LangfuseDatasetAdapter`, `LocalJSONDatasetAdapter`, `FallbackDatasetAdapter`,
`CallableEvaluatorAdapter`, `PydanticEvalsLLMJudgeAdapter`, `PydanticEvalsRunner`, `LangfuseArtefactStore`,
`LocalJSONArtefactStore` — explicitly subclasses its `base.py` ABC. This is real inheritance, not structural
typing: instantiating an incomplete subclass raises `TypeError`, and `isinstance(adapter, DatasetPort)` is a
meaningful assertion in tests.

`record_case` and `finish_run` are synchronous by design, matching how the current Langfuse path already
works: `ctx.client.create_score(...)` today is a queued, non-blocking call inside the Langfuse SDK client,
flushed later via `langfuse_utils.flush()`. The port preserves that behaviour rather than introducing a new
async requirement.

## Adapters

### Dataset adapters

- **`LangfuseDatasetAdapter`** wraps `client.get_dataset(...)`, converts each `DatasetItem` into a `Case`,
  and keeps a `native_item(case_id)` lookup so `LangfuseArtefactStore` can link results back to the original
  Langfuse dataset item.
- **`LocalJSONDatasetAdapter`** loads cases from `evals/data/<dataset>/`, building on the
  Langfuse-vs-local-JSON duality already present in `datasets.py::load_local_data`.
- **`FallbackDatasetAdapter`** tries a primary `DatasetPort` and falls back to a secondary one on
  `DatasetNotFoundError`. It logs a warning when the fallback triggers, so a genuine Langfuse
  auth/connectivity failure is never silently mistaken for an intentionally offline run.

### Evaluator adapter

**`CallableEvaluatorAdapter`** normalises the `Evaluation | dict | list[...]` return shapes that
`evals/evaluators/`'s factories already produce into `list[Score]`. This replaces the normalization block
that today is copy-pasted into every stage file (e.g. `eval_condensation.py:135-150`).

Its wrapped callables are a mix of sync and async: 5 of the 7 evaluator factories (`groundedness`,
`coverage`, `title_specificity`, `condensation_quality`, `refinement_quality`) return `async def` callables
(retried internally via a shared `_invoke_with_retry` helper), while `mapping_f1_evaluator` and the
redundancy callable stay sync. `CallableEvaluatorAdapter.evaluate()` handles both —
`result = await fn(...) if inspect.iscoroutinefunction(fn) else fn(...)` — rather than assuming every
wrapped callable is one or the other.

**`PydanticEvalsLLMJudgeAdapter`** wraps `pydantic_evals.evaluators.LLMJudge` behind the same `EvaluatorPort`
— the planned home for the team's expected future migration of `evaluators.py`'s LLM-judge functions onto
pydantic-evals' own judge primitive, per ADR-0011's "use pydantic-evals for LAJ" mandate. Built and
unit-tested this pass (stubbed `LLMJudge`, no network); not wired into any `StageConfig` yet — retiring an
`evaluators.py` function is an output-quality-parity judgment call for a dedicated future pass, not a side
effect of this one.

```python
class PydanticEvalsLLMJudgeAdapter(EvaluatorPort):
    def __init__(self, name: str, rubric: str, model: Any = None):
        self._name = name
        self._judge = pydantic_evals.evaluators.LLMJudge(rubric=rubric, model=model)

    async def evaluate(self, case: Case, output: Any) -> list[Score]:
        ctx = pydantic_evals.evaluators.EvaluatorContext(
            name=case.id, inputs=case.inputs, output=output,
            expected_output=case.expected_output, metadata=case.metadata,
        )
        result = await self._judge.evaluate(ctx)
        return [Score(name=self._name, value=float(result.value), comment=result.reason or "")]
```

(`LLMJudge`'s and `EvaluatorContext`'s exact constructor kwargs above are reconstructed from general
knowledge of the library's shape, not verified against a fresh doc fetch — confirm against the installed
`pydantic-evals` version before implementing; the pattern — build an `EvaluatorContext` from our `Case`, call
the native judge, translate its result into our `Score` — is the right shape regardless of exact kwarg names.)

This has to go through `EvaluatorPort`, not bypass it. The shortcut of handing `LLMJudge` instances straight
to `pydantic_evals.Dataset(evaluators=[...])` inside `PydanticEvalsRunner` only works while `PydanticEvalsRunner`
is the active runner — the moment a `StageConfig` mixes a bypassed-native evaluator with any other runner
(`InlineSequentialRunner` included), that evaluator silently can't run, breaking the swappability the whole
framework is built around for that one evaluator. Wrapping it costs one adapter file and keeps every
evaluator — native or hand-rolled — runnable under every runner. The migration path this unlocks:
`StageConfig.build_evaluators` returns `list[EvaluatorPort]`, and nothing stops that list from mixing adapter
types — `groundedness` could move to `PydanticEvalsLLMJudgeAdapter` while `coverage` stays on
`CallableEvaluatorAdapter`, one evaluator at a time, with zero change to `run_stage`, either runner, or any
artefact store.

### Runner adapter

**`PydanticEvalsRunner`** wraps `pydantic_evals.Dataset.evaluate`. Internally it builds a
`pydantic_evals.Dataset(cases=[...], evaluators=[_EvaluatorBridge(...)])` and calls `.evaluate(task,
max_concurrency=...)`. `_EvaluatorBridge(pydantic_evals.evaluators.Evaluator)` fans a pydantic-evals
`EvaluatorContext` (exposing `.inputs`, `.output`, `.expected_output`, `.metadata`, `.name`) out to the
framework's own `EvaluatorPort` list, and translates the results back into pydantic-evals' expected return
shape. It also populates `RunReport.engine_report` with the native `EvaluationReport` object `Dataset.
evaluate()` returns — see [Surfacing pydantic-evals' native EvaluationReport](#surfacing-pydantic-evals-native-evaluationreport-without-widening-the-ports)
below. Every other runner (`InlineSequentialRunner` included) leaves `engine_report` at its default, `None`.

### Artefact store adapters

- **`LangfuseArtefactStore`** mirrors the trace/score-pushing logic currently duplicated in every
  `_run_with_langfuse`. Its `finish_run()` flushes the Langfuse context — but only if `EvalBackends.
  context_owned` is `True` (see below), so a context supplied by a caller like `benchmark.py` is never
  flushed twice. It's also the only adapter that unpacks `engine_report` when `finish_run()` receives one.
- **`LocalJSONArtefactStore`** writes results under `evals/local_eval_runs/<stage>/` — deliberately not
  `evals/benchmark_results/`, which `benchmark.py` already owns as a timestamp-keyed directory
  (`benchmark_results/<benchmark_id>/benchmark.log`) that `visualise_benchmark.py` scans expecting only
  timestamp children. `local_eval_runs/` is a strict improvement over today's local fallback, which never
  persisted anything at all — but it's a separate, non-interchangeable output tree from `benchmark.py`'s
  results directory. `visualise_benchmark.py` doesn't import any `eval_*.py` module today (it only reads
  persisted Langfuse/`benchmark_results` data) and isn't updated to read `local_eval_runs/` in this pass.

Both return the same flat `dict[str, Any]` shape `benchmark.py` already parses (see below).

### Surfacing pydantic-evals' native `EvaluationReport` without widening the ports

`RunReport.engine_report` is how `PydanticEvalsRunner`'s native `EvaluationReport` reaches
`LangfuseArtefactStore` without breaking swappability — worth spelling out exactly why this doesn't
compromise the port design, since it's the one place a runner-specific object crosses an adapter boundary:

- `ArtefactStorePort.finish_run` gains one optional, keyword-only parameter, typed `Any`. No `pydantic_evals`
  import appears in `base.py`, `eval_types.py`, or `stage_runner.py` — the ABCs stay completely
  engine-agnostic.
- `PydanticEvalsRunner.run()` populates `RunReport(outcomes=[...], engine_report=raw_report)`, where
  `raw_report` is the actual `pydantic_evals.reporting.EvaluationReport` from `Dataset.evaluate()`. Every
  other runner leaves the default `None` — additive, not a new obligation on every adapter.
- `stage_runner.run_stage()` passes it straight through: `backends.artefacts.finish_run(handle,
  engine_report=report.engine_report)`.
- `LocalJSONArtefactStore.finish_run(self, run_handle, *, engine_report=None)` ignores the parameter
  entirely — no pydantic-evals awareness, no behaviour change.
- `LangfuseArtefactStore.finish_run(self, run_handle, *, engine_report=None)` is the only adapter that
  unpacks it, defensively: `if engine_report is not None and isinstance(engine_report, pydantic_evals.
  reporting.EvaluationReport): ...`. The `isinstance` check matters — `engine_report` is `Any` by contract,
  so a future second engine could populate it with something else entirely, and `LangfuseArtefactStore` must
  not assume it's always a pydantic-evals type. Importing `pydantic_evals.reporting` inside
  `langfuse_adapter.py` is an acceptable, narrow coupling: this file is already Langfuse-specific by design,
  and `pydantic-evals` and `langfuse` already ship together in the same `eval` extras group, so it isn't a
  new dependency requirement.
- The swappability test stays meaningful: it asserts `engine_report is None` for the `InlineSequentialRunner`
  run and not for the `PydanticEvalsRunner` run — an explicit demonstration that the escape hatch is
  additive, not load-bearing for the core `outcomes`/`scores` comparison.

**What `LangfuseArtefactStore` does with it, this pass:** call `engine_report.print()` (or equivalent) for a
richer console summary at the end of a run, and/or pull per-case timing data pydantic-evals already tracks
into the score dict as extra metadata — both safe, mechanical wins with the shape verified above.

**Real follow-up, not this pass:** whether pydantic-evals' own OpenTelemetry instrumentation (if `Dataset.
evaluate()` emits per-case/per-evaluator spans) can feed Langfuse more directly than the current hand-rolled
`dataset_item_trace`/`ctx.client.create_score(...)` bookkeeping. That's a materially bigger change — it would
touch how traces get *created*, not just how the final summary gets built — and its feasibility depends on
exact `pydantic-evals`/Langfuse SDK version behaviour not verified in this pass. Worth a dedicated spike
before committing to it.

## Orchestration

### `evals/config.py::resolve_backends`

```python
@dataclass
class EvalBackends:
    dataset: DatasetPort
    artefacts: ArtefactStorePort
    runner: EvalRunnerPort
    context_owned: bool = False   # True when resolve_backends() constructed the Langfuse context itself
                                   # (context was None); LangfuseArtefactStore.finish_run() flushes iff this
                                   # is True.

def resolve_backends(context: Any | None, *, stage: str, dataset: str) -> EvalBackends: ...
```

This is the **only** orchestration function anywhere that touches `langfuse_utils` / `LangfuseContext`
directly (besides the Langfuse adapter modules themselves):

- If `context` is `None`, it builds a default one via `langfuse_utils.get_langfuse_context(...)` and sets
  `context_owned=True` on the `EvalBackends` it returns.
- If the resulting context is enabled, it wires up the Langfuse-backed adapters; otherwise, the local-only
  ones.
- It picks the runner via one environment variable, `THEMEFINDER_EVAL_ENGINE` (default `pydantic_evals`),
  read once at the top of the function — the explicit seam a second engine plugs into later. There is no
  plugin registry; this is deliberately simple.

### `evals/stage_runner.py::run_stage`

```python
async def run_stage(stage: StageConfig, dataset: str, backends: EvalBackends, llm, judge_llm=None) -> dict:
    ...
```

Loads cases via `backends.dataset`, builds evaluators via `StageConfig.build_evaluators`, runs the task via
`backends.runner`, records and finishes via `backends.artefacts`. Pure ports — no `langfuse` or
`pydantic_evals` import, no conditional branching on context state. This is the one function all four stage
scripts delegate to, and the function the swappability test exercises directly with fake backends.

### The four stage scripts

```python
# eval_generation.py / eval_mapping.py / eval_condensation.py / eval_refinement.py
async def evaluate_generation(dataset="gambling_XS", llm=None, judge_llm=None, context=None) -> dict:
    llm = llm or _default_llm()
    backends = resolve_backends(context, stage=STAGE.stage, dataset=dataset)
    return await run_stage(STAGE, dataset, backends, llm, judge_llm)
```

Each script collapses from roughly 300 lines to a `_task(inputs, llm)` async function, a module-level
`StageConfig`, the thin wrapper above, and the unchanged CLI/`__main__` block. `_run_with_langfuse` /
`_run_local_fallback` are deleted, not relocated.

`eval_mapping.py` keeps its existing `question_num: int | None = None` parameter to reproduce its
`--question` CLI flag — but its wrapper does **not** mutate the module-level `StageConfig`. It builds a
per-call config instead: `dataclasses.replace(STAGE, case_filter=...)` when `question_num` is given, the
unmodified `STAGE` otherwise. `benchmark.py` never passes `question_num`, so its calls always see the
unfiltered `STAGE` regardless of what any concurrent or prior CLI invocation did in the same process —
mutating the shared module-level object would have made a CLI `--question 2` run capable of leaking a filter
into an unrelated `benchmark.py` run. All four `evaluate_X` wrappers otherwise share one signature —
`(dataset, llm, judge_llm, context)` — with `question_num` as `evaluate_mapping`'s only addition.
`evaluate_mapping` accepts `judge_llm` too, for signature uniformity, even though `StageConfig.
build_evaluators` for mapping ignores it (`mapping_f1_evaluator` is a deterministic F1 metric, not an LLM
judge) — consistent with `benchmark.py`'s existing `evals_with_judge` set, which already never passes
`judge_llm` to mapping.

**Scoring-consistency status per stage:** generation, condensation, and refinement are already consistent —
each already calls the same `evaluators.py` LLM-judge suite in both its local and Langfuse paths, so this
plan doesn't change their local-run scoring. **Mapping is the one stage this plan changes local-run
behaviour for**: its local fallback currently calls `metrics.py::calculate_mapping_metrics`, while `run_stage`
calls `StageConfig.build_evaluators` — which wraps `evaluators.py::mapping_f1_evaluator` — regardless of
dataset source. Mapping's local runs switch onto `mapping_f1_evaluator` as a direct structural consequence of
adopting `run_stage`, not a special extra step. `evals/metrics.py` is deleted outright as part of this pass:
`eval_mapping.py::calculate_mapping_metrics` is its only remaining importer (`eval_generation.py` no longer
imports it, `eval_condensation.py`/`eval_refinement.py` never did).

## Compatibility contract with benchmark.py

`benchmark.py` calls each stage's `evaluate_X(dataset=..., llm=..., context=..., judge_llm=...)` and expects
a flat `dict[str, Any]` back, which it splits via `isinstance(value, (int, float))` into `scores` vs
`outputs`. It also owns opening the Langfuse trace context itself and later calls
`langfuse_utils.extract_session_metrics(session_id=...)` for cost/token data.

Every stage function keeps this exact shape, and Langfuse traces stay queryable by `session_id`. The only
change inside `benchmark.py` is a one-line kwarg rename at its call site: `"langfuse_ctx": langfuse_ctx`
becomes `"context": langfuse_ctx`. The local variable name inside `benchmark.py` is unaffected — only the
kwarg key crossing into the now-generic stage function signature changes. This is what makes "zero
Langfuse-specific code in the stage scripts" achievable without touching how `benchmark.py` itself talks to
Langfuse.

## Configuration strategy

Environment variables are the right mechanism for `evals/` config — it already reads config exclusively via
`os.getenv()`, with no config-file infrastructure anywhere in the package, so a file-based format would be
inconsistent with the existing convention and adds parsing overhead for no benefit at this scale. `THEMEFINDER_EVAL_ENGINE`
follows that convention.

But "env var" and "an ad hoc `os.getenv()` call in whichever file happens to need it, independently of every
other file that needs the same value" are two different decisions. This framework makes the first and fixes
the second.

### The problem, scoped and measured

Checked first against the rest of the monorepo, not assumed: `backend/` already has a proper Django settings
module (`backend/settings/{base,local,production,test}.py}`) and its handful of `os.getenv`/`os.environ` hits
are idiomatic Django bootstrap (`os.environ.setdefault("DJANGO_SETTINGS_MODULE", ...)`) or single-purpose
reads — not sprawl. `lambda/*` and `pipeline-*/` are independently-deployed units with no shared caller, so a
per-file env read there carries no drift risk. The real problem is scoped to `themefinder/evals/`: one
importable package, many modules, each independently reaching into `os.environ` for overlapping config.

Grep-verified inventory (excluding `evals/metrics.py`, deleted outright in this pass — see
[Rollout sequencing](#rollout-sequencing) — so not worth migrating first):

| Env var | Read independently in | Call sites |
|---|---|---|
| `AUTO_EVAL_4_1_SWEDEN_DEPLOYMENT` | `eval_generation.py`, `eval_condensation.py`, `eval_mapping.py`, `eval_refinement.py`, `langfuse_utils.py` | 5 |
| `LANGFUSE_SECRET_KEY` / `PUBLIC_KEY` / `BASE_URL` | `langfuse_utils.py`, `benchmark.py::query_langfuse_costs()` (builds its own `Langfuse` client from a second, independent read) | 2 |
| `LANGFUSE_BASE_URL` / `LANGFUSE_PROJECT_ID` | `visualise_benchmark.py` | adds a 3rd site for `LANGFUSE_BASE_URL` |
| `LLM_GATEWAY_URL` / `CONSULT_EVAL_LITELLM_API_KEY` | `utils_gateway.py` | 1 (already fine) |
| `ENVIRONMENT`, `GITHUB_SHA` | `langfuse_utils.py` | 1 (already fine) |
| `THEMEFINDER_EVAL_ENGINE` (new) | `config.py::resolve_backends` | 1 (new, single-sited by construction) |

Separately, `dotenv.load_dotenv()` is called independently in 7 files (`benchmark.py`, all four `eval_*.py`,
`visualise_benchmark.py`, `generate_synthetic.py`) — the same "everyone re-does the same setup" problem one
level up.

### `evals/settings.py`

```python
# deliberately not named config.py — that name is already taken by evals/config.py, which wires
# adapters together; this module just reads the environment, once.
from dataclasses import dataclass
from functools import lru_cache
import os
import dotenv

@dataclass(frozen=True)
class EvalSettings:
    auto_eval_deployment: str | None
    llm_gateway_url: str | None
    llm_gateway_api_key: str | None
    langfuse_secret_key: str | None
    langfuse_public_key: str | None
    langfuse_base_url: str | None
    langfuse_project_id: str | None
    environment: str
    git_sha: str
    eval_engine: str

@lru_cache(maxsize=1)
def get_settings() -> EvalSettings:
    dotenv.load_dotenv()
    return EvalSettings(
        auto_eval_deployment=os.getenv("AUTO_EVAL_4_1_SWEDEN_DEPLOYMENT"),
        llm_gateway_url=os.getenv("LLM_GATEWAY_URL"),
        llm_gateway_api_key=os.getenv("CONSULT_EVAL_LITELLM_API_KEY"),
        langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        langfuse_base_url=os.getenv("LANGFUSE_BASE_URL"),
        langfuse_project_id=os.getenv("LANGFUSE_PROJECT_ID"),
        environment=os.getenv("ENVIRONMENT", "development"),
        git_sha=os.getenv("GITHUB_SHA", "local")[:7],
        eval_engine=os.getenv("THEMEFINDER_EVAL_ENGINE", "pydantic_evals"),
    )
```

`get_settings()` is a process-wide cached singleton: env vars are read once and `.env` is loaded once,
regardless of how many modules ask. `frozen=True` means nothing can mutate it after construction.

**Dependency injection lands exactly at the boundaries that already have one** — `resolve_backends` and the
two existing shared helper functions each grow an optional `settings: EvalSettings | None = None` parameter,
defaulting to `get_settings()`, the same optional-with-a-default pattern `context` already uses:

- `resolve_backends(context=None, *, stage, dataset, settings=None)` reads `settings.eval_engine` instead of
  `os.getenv("THEMEFINDER_EVAL_ENGINE", ...)` directly, and forwards `settings` when it builds a default
  Langfuse context.
- `langfuse_utils.get_langfuse_context(session_id, eval_type, metadata=None, tags=None, settings=None)` reads
  `settings.langfuse_secret_key` / `.langfuse_public_key` / `.langfuse_base_url` / `.environment` / `.git_sha`
  / `.auto_eval_deployment` internally. **No caller changes** — `benchmark.py` calls it exactly as before.
- `utils_gateway.gateway_credentials(settings=None)` reads `settings.llm_gateway_url` /
  `.llm_gateway_api_key` internally. Every existing call site (`base_url, api_key =
  utils_gateway.gateway_credentials()`, present in all four `eval_*.py` files) is unchanged.
- `benchmark.py::query_langfuse_costs()`'s 3 independent reads become `get_settings()` reads, removing the
  duplicate credential logic without changing behaviour.
- `visualise_benchmark.py`'s 2 reads become `get_settings()` reads.
- The 5 inline `os.getenv("AUTO_EVAL_4_1_SWEDEN_DEPLOYMENT")` sites building each stage's default task LLM
  become `get_settings().auto_eval_deployment` — a direct read, no DI needed since these are leaf
  construction sites already guarded by `if llm is None` (only exercised in ad hoc runs, never in tests that
  inject a fake LLM).
- All 7 explicit `dotenv.load_dotenv()` calls are deleted — `get_settings()` already guarantees `.env` is
  loaded before any field is read.

This keeps "zero Langfuse code in the four stage scripts" intact: the stage scripts only ever read
`get_settings().auto_eval_deployment`, a plain `str | None` — no Langfuse import, no Langfuse-named field
touched. `EvalSettings` bundles Langfuse fields alongside non-Langfuse ones; the stage scripts simply never
reach for the ones with "langfuse" in the name.

### Test impact: a real correctness risk, not just style

`test_benchmark.py` and `test_utils_gateway.py` already have 12 `monkeypatch.setenv(...)` calls between them.
A naive `@lru_cache` singleton would silently break both: the first test to call `get_settings()` poisons the
cache for every later test expecting a different env var value, since `lru_cache` never re-reads after the
first call. Fix — one autouse fixture in `evals/tests/conftest.py`:

```python
@pytest.fixture(autouse=True)
def _reset_eval_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
```

This runs before and after every test, so the existing `monkeypatch.setenv` usage keeps working with zero
changes to `test_benchmark.py` or `test_utils_gateway.py` themselves — only `conftest.py` gets the addition.

## Rollout sequencing

Each phase is independently revertible; nothing is broken in between phases.

1. **Groundwork** — extras group in `pyproject.toml`, workflow YAML updates, `eval_types.py` +
   empty `adapters/` package scaffolding with all four `base.py` ABCs (additive, unused). Move
   `langfuse_utils.py` → `utils/langfuse_utils.py` and `utils.py` → `utils/prompt_utils.py`, updating the two
   long-term import sites (`benchmark.py`, `generate_synthetic.py`). Add `evals/settings.py` and the autouse
   `_reset_eval_settings_cache()` fixture *before* anything depends on it, then migrate
   `utils_gateway.gateway_credentials()`, `utils/langfuse_utils.get_langfuse_context()`,
   `benchmark.py::query_langfuse_costs()`, and `visualise_benchmark.py`'s two reads onto it — removing their
   `os.getenv()` calls and (outside the four `eval_*.py` files, handled in step 5) their `dotenv.load_dotenv()`
   calls. Verify the existing `monkeypatch.setenv`-based tests in `test_benchmark.py`/`test_utils_gateway.py`
   still pass.
2. **Dataset adapters** — `local_json_adapter.py`, `langfuse_adapter.py`, `fallback_adapter.py`, tested
   against real `evals/data/gambling_XS` fixtures.
3. **Evaluator split + adapters** — split flat `evaluators.py` into `evals/evaluators/`, function bodies moved
   verbatim; add `llm_judge_adapter.py` importing from the new package. Also add
   `pydantic_evals_llm_judge_adapter.py` (`PydanticEvalsLLMJudgeAdapter`), unit-tested against a stubbed
   `LLMJudge` — built and proven, not wired into any `StageConfig`.
4. **Runner + artefact adapters + shared runner** — `pydantic_evals_adapter.py` (populates `RunReport.
   engine_report`), both artefact store adapters (`langfuse_adapter.py`'s `finish_run` unpacks
   `engine_report` when present), `config.py`, `stage_runner.py`, and the test fakes. Nothing
   production-facing changes yet; the swappability test runs fully offline at this point.
5. **Migrate stage modules one at a time** — `eval_generation.py` first (most complex: three-stage pipeline,
   four evaluators), then `eval_mapping.py`, `eval_condensation.py`, `eval_refinement.py`. The one-line
   `benchmark.py` kwarg rename lands alongside the first migration. For each stage: drop its
   `dotenv.load_dotenv()` call and swap its inline `os.getenv("AUTO_EVAL_4_1_SWEDEN_DEPLOYMENT")` for
   `get_settings().auto_eval_deployment`; run before and after against `gambling_XS`, with and without
   `LANGFUSE_*` env vars set, and diff the returned score dict (expected to match for every stage except
   mapping, whose local-path score dict changes shape from `calculate_mapping_metrics`'s keys to
   `mapping_f1_evaluator`'s — the one disclosed behaviour change, see above). Once `eval_mapping.py` is
   migrated — its `from metrics import calculate_mapping_metrics` line gone, the only remaining
   `evals/metrics.py` import — delete `evals/metrics.py` outright.
6. **Cleanup note only** — confirm `utils/langfuse_utils.py` is still needed only by `benchmark.py`,
   `generate_synthetic.py`, and the two Langfuse adapters; note (without implementing) how `benchmark.py`
   could later call `resolve_backends`/`run_stage` directly, and how `evals/synthetic/` could target
   `DatasetPort`. The `os.getenv()` centralisation and the `evals/metrics.py` deletion are both done in steps
   1 and 5, not deferred.

## Testing strategy

- `evals/tests/fakes.py` provides `FakeDatasetPort`, `FakeEvaluatorPort`, `FakeArtefactStore` (each
  subclassing the real ABC) and `InlineSequentialRunner` — a ~15-line loop implementing `EvalRunnerPort` with
  zero pydantic-evals dependency.
- **Swappability proof** (`test_stage_runner.py`): the same fake cases, evaluators, and task run once through
  `PydanticEvalsRunner()` and once through `InlineSequentialRunner()`, asserting identical `RunReport.
  outcomes`/`scores` — the one expected difference, `engine_report` (populated for `PydanticEvalsRunner`,
  `None` otherwise), is asserted explicitly rather than silently ignored. This is the concrete evidence the
  abstraction isn't paper-thin — it's what would catch any accidental coupling of evaluator, dataset, or
  artefact logic to pydantic-evals internals.
- **LAJ adapter proof** (`test_evaluator_adapters.py`): `PydanticEvalsLLMJudgeAdapter`, built against a
  stubbed `LLMJudge`, passes the same ABC-subclass checks as every other evaluator adapter, and its
  `evaluate()` output matches the `list[Score]` shape `CallableEvaluatorAdapter` produces — proving a native
  pydantic-evals judge and a hand-rolled `evaluators.py` judge are genuinely interchangeable in a
  `StageConfig.build_evaluators` list.
- Each adapter has its own offline unit test (`test_dataset_adapters.py`, `test_evaluator_adapters.py`,
  `test_artefact_store.py`), each asserting the concrete adapter is a genuine subclass of its ABC and that
  instantiating an incomplete subclass raises `TypeError`.
- A grep-based check enforces the zero-Langfuse-in-scripts rule directly:
  `grep -ril langfuse evals/eval_*.py evals/stage_runner.py evals/eval_types.py evals/adapters/*/base.py
  evals/evaluators/*.py` must return nothing.
- A second grep-based check enforces the `os.getenv()` centralisation directly: `grep -rn "os\.getenv\|os\.
  environ\.get" evals/*.py` returns only one line per var inside `evals/settings.py::get_settings()`, plus
  `benchmark.py`'s unrelated `GRPC_DNS_RESOLVER` process-level workaround (not app config, not migrated).
  `grep -rn load_dotenv evals/*.py` returns only `evals/settings.py`. `evals/metrics.py` no longer exists.
- The `evaluators.py` and `langfuse_utils.py` splits are checked for byte-level fidelity: the concatenation of
  the new files' non-boilerplate content is diffed against the pre-split file at `git show HEAD:...` to
  confirm relocation only, no rewriting.
- `pytest tests/ -v` (95% coverage gate) and `pytest evals/tests/ -v` — including the untouched
  `test_benchmark.py` and `test_utils_gateway.py`, whose 12 `monkeypatch.setenv` calls keep passing via the
  new autouse cache-clearing fixture — stay green throughout every phase.

## Deferred to a later pass

- Adapting `benchmark.py` to call `resolve_backends`/`run_stage` directly instead of the four stage-script
  wrappers.
- Adapting `evals/synthetic/` to target `DatasetPort` instead of talking to Langfuse directly.
- Actually migrating any of `evaluators.py`'s five LLM-judge functions onto `PydanticEvalsLLMJudgeAdapter` —
  the adapter exists and is tested this pass, but retiring a hand-rolled judge is an output-quality-parity
  decision, not a mechanical one.
- Investigating whether pydantic-evals' native OpenTelemetry instrumentation can feed Langfuse traces more
  directly than the current hand-rolled `dataset_item_trace`/`ctx.client.create_score(...)` bookkeeping —
  a bigger change than the `engine_report` escape hatch, not verified against actual SDK behaviour this pass.
