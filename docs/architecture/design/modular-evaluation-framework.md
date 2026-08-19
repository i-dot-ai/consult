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
paths. Worse, the two paths don't even share scoring logic: the Langfuse path uses the full `evaluators.py`
LLM-judge suite, the local fallback uses cheaper stats from `metrics.py`. As a direct result, `langfuse` is a
core, non-optional dependency of the package purely to support this duplication.

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
- `evals/metrics.py` (the old local-fallback scoring) becomes unused but is not deleted.
- Consolidating the codebase's scattered `os.getenv()` calls into a single settings object is noted as a
  follow-up, not implemented here (see [Configuration strategy](#configuration-strategy)).

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
    def finish_run(self, run_handle: Any) -> dict: ...
```

Every concrete adapter — `LangfuseDatasetAdapter`, `LocalJSONDatasetAdapter`, `FallbackDatasetAdapter`,
`CallableEvaluatorAdapter`, `PydanticEvalsRunner`, `LangfuseArtefactStore`, `LocalJSONArtefactStore` —
explicitly subclasses its `base.py` ABC. This is real inheritance, not structural typing: instantiating an
incomplete subclass raises `TypeError`, and `isinstance(adapter, DatasetPort)` is a meaningful assertion in
tests.

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

### Runner adapter

**`PydanticEvalsRunner`** wraps `pydantic_evals.Dataset.evaluate`. Internally it builds a
`pydantic_evals.Dataset(cases=[...], evaluators=[_EvaluatorBridge(...)])` and calls `.evaluate(task,
max_concurrency=...)`. `_EvaluatorBridge(pydantic_evals.evaluators.Evaluator)` fans a pydantic-evals
`EvaluatorContext` (exposing `.inputs`, `.output`, `.expected_output`, `.metadata`, `.name`) out to the
framework's own `EvaluatorPort` list, and translates the results back into pydantic-evals' expected return
shape.

### Artefact store adapters

- **`LangfuseArtefactStore`** mirrors the trace/score-pushing logic currently duplicated in every
  `_run_with_langfuse`. Its `finish_run()` flushes the Langfuse context — but only if `EvalBackends.
  context_owned` is `True` (see below), so a context supplied by a caller like `benchmark.py` is never
  flushed twice.
- **`LocalJSONArtefactStore`** writes results under `evals/benchmark_results/<stage>/` — a strict
  improvement over today's local fallback, which never persisted anything at all.

Both return the same flat `dict[str, Any]` shape `benchmark.py` already parses (see below).

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
`_run_local_fallback` are deleted, not relocated. `eval_mapping.py` additionally sets `StageConfig.
case_filter` to reproduce its `--question` CLI flag.

**Deliberate, disclosed behaviour change:** local (no-Langfuse) runs now get the same LLM-judge suite as
Langfuse runs, instead of the cheaper `metrics.py` stats — removing the inconsistency that existed between
the two paths today. `evals/metrics.py` becomes unused as a result; it's left in place as a follow-up
deletion candidate rather than removed in this pass.

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

`THEMEFINDER_EVAL_ENGINE` is the only new environment variable this framework introduces, and an environment
variable is the right mechanism for it. `evals/` already reads a dozen environment variables via ad hoc
`os.getenv()` calls scattered across `benchmark.py`, `langfuse_utils.py`, `utils_gateway.py`, and every
`eval_*.py` — `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_BASE_URL`, `AUTO_EVAL_4_1_SWEDEN_
DEPLOYMENT`, `LLM_GATEWAY_URL`, `CONSULT_EVAL_LITELLM_API_KEY`, `ENVIRONMENT`, `GITHUB_SHA`,
`LANGFUSE_PROJECT_ID` — with no config-file infrastructure anywhere in the package. Introducing a file-based
format for a single switch would be inconsistent with the existing convention and adds parsing overhead with
no real benefit at this scale.

The scattered-`os.getenv()` pattern itself is a pre-existing smell this framework doesn't fix. A future pass
could centralise these into one small settings object — a `dataclass` or `pydantic.BaseSettings` built once
and passed into adapters as a constructor argument, rather than each adapter or helper reaching into
`os.environ` directly. That's out of scope here because it touches `utils_gateway.py` and `benchmark.py`,
both otherwise untouched or minimally touched by this pass; it's noted as a follow-up alongside the
`evals/metrics.py` deletion.

## Rollout sequencing

Each phase is independently revertible; nothing is broken in between phases.

1. **Groundwork** — extras group in `pyproject.toml`, workflow YAML updates, `eval_types.py` +
   empty `adapters/` package scaffolding with all four `base.py` ABCs (additive, unused). Move
   `langfuse_utils.py` → `utils/langfuse_utils.py` and `utils.py` → `utils/prompt_utils.py`, updating the two
   long-term import sites (`benchmark.py`, `generate_synthetic.py`).
2. **Dataset adapters** — `local_json_adapter.py`, `langfuse_adapter.py`, `fallback_adapter.py`, tested
   against real `evals/data/gambling_XS` fixtures.
3. **Evaluator split + adapter** — split flat `evaluators.py` into `evals/evaluators/`, function bodies moved
   verbatim; add `llm_judge_adapter.py` importing from the new package.
4. **Runner + artefact adapters + shared runner** — `pydantic_evals_adapter.py`, both artefact store
   adapters, `config.py`, `stage_runner.py`, and the test fakes. Nothing production-facing changes yet; the
   swappability test runs fully offline at this point.
5. **Migrate stage modules one at a time** — `eval_generation.py` first (most complex: three-stage pipeline,
   four evaluators), then `eval_mapping.py`, `eval_condensation.py`, `eval_refinement.py`. The one-line
   `benchmark.py` kwarg rename lands alongside the first migration. For each stage: run before and after
   against `gambling_XS`, with and without `LANGFUSE_*` env vars set, and diff the returned score dict.
6. **Cleanup note only** — confirm `utils/langfuse_utils.py` is still needed only by `benchmark.py`,
   `generate_synthetic.py`, and the two Langfuse adapters; flag `evals/metrics.py` and the settings
   consolidation as follow-up candidates; note (without implementing) how `benchmark.py` could later call
   `resolve_backends`/`run_stage` directly, and how `evals/synthetic/` could target `DatasetPort`.

## Testing strategy

- `evals/tests/fakes.py` provides `FakeDatasetPort`, `FakeEvaluatorPort`, `FakeArtefactStore` (each
  subclassing the real ABC) and `InlineSequentialRunner` — a ~15-line loop implementing `EvalRunnerPort` with
  zero pydantic-evals dependency.
- **Swappability proof** (`test_stage_runner.py`): the same fake cases, evaluators, and task run once through
  `PydanticEvalsRunner()` and once through `InlineSequentialRunner()`, asserting identical `RunReport`
  output. This is the concrete evidence the abstraction isn't paper-thin — it's what would catch any
  accidental coupling of evaluator, dataset, or artefact logic to pydantic-evals internals.
- Each adapter has its own offline unit test (`test_dataset_adapters.py`, `test_evaluator_adapters.py`,
  `test_artefact_store.py`), each asserting the concrete adapter is a genuine subclass of its ABC and that
  instantiating an incomplete subclass raises `TypeError`.
- A grep-based check enforces the zero-Langfuse-in-scripts rule directly:
  `grep -ril langfuse evals/eval_*.py evals/stage_runner.py evals/eval_types.py evals/adapters/*/base.py
  evals/evaluators/*.py` must return nothing.
- The `evaluators.py` and `langfuse_utils.py` splits are checked for byte-level fidelity: the concatenation of
  the new files' non-boilerplate content is diffed against the pre-split file at `git show HEAD:...` to
  confirm relocation only, no rewriting.
- `pytest tests/ -v` (95% coverage gate) and `pytest evals/tests/ -v` — including the untouched
  `test_benchmark.py` and `test_utils_gateway.py` — stay green throughout every phase.

## Deferred to a later pass

- Adapting `benchmark.py` to call `resolve_backends`/`run_stage` directly instead of the four stage-script
  wrappers.
- Adapting `evals/synthetic/` to target `DatasetPort` instead of talking to Langfuse directly.
- Deleting `evals/metrics.py` once confirmed fully unused.
- Consolidating the scattered `os.getenv()` calls across the eval suite into a single settings object.
