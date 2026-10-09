# Modular Evaluation Framework for Themefinder

This is the detailed design behind [ADR-0013](../decisions/0013-modular-evaluation-framework-for-themefinder.md). The ADR
records the decision and its consequences; this document is the reference for how the framework is actually
built — directory layout, types, interfaces, and the rules that keep it swappable in practice, not just in
theory.

Everything here lives under `themefinder/evals/`.

## Problem

`themefinder/evals/` has a working LLM-quality evaluation framework: LLM-judge evaluators, dataset loading,
Langfuse tracing, a multi-model benchmark runner, synthetic data generation. But the execution engine and the
artefact store are hard-wired together. Each of the four component eval scripts —
`eval_generation.py`, `eval_mapping.py`, `eval_condensation.py`, `eval_refinement.py` — writes its own custom
`_run_with_langfuse(...)` / `_run_local_fallback(...)` branch, duplicating most of its logic across both
paths. Mapping is the one component where the two paths don't even share scoring logic: its Langfuse path calls
`evaluators.py::mapping_f1_evaluator`, its local fallback calls a separate sklearn-based implementation,
`metrics.py::calculate_mapping_metrics`. Generation, condensation, and refinement are already consistent —
each already calls the same `evaluators.py` LLM-judge functions in both paths. As a direct result, `langfuse`
is a core, non-optional dependency of the package purely to support the duplication.

## Goals

- pydantic-evals is the execution engine: it owns case iteration, concurrency, retries, and reporting.
- Langfuse is dataset + artefact storage only — not the orchestrator.
- Both the engine and the storage backend are genuinely swappable, proven by a test, not just structurally
  possible.
- Zero Langfuse- or pydantic-evals-specific code in component definitions and the unified API/CLI.
- Migrate in place, incrementally, with each phase independently revertible.
- DVC drives reproducible eval runs: a `dvc.yaml` pipeline wraps the same entry points every other caller
  uses, giving dependency-aware caching (skip a component when nothing it depends on changed) and experiment
  tracking (`dvc exp run`/`dvc metrics show`) for comparing intentional variations.

## Non-goals (this pass)

- `benchmark.py` keeps its Langfuse tracing and cost collection. Only component execution moves to the unified
  API; it is not rewritten to manage the ports directly.
- `evals/synthetic/` and its CLI entry point `generate_synthetic.py` (synthetic data generation) are
  untouched. The Langfuse coupling here lives entirely in `generate_synthetic.py`'s own `LangfuseContext`
  construction, trace wrap, and flush — the `evals/synthetic/` package it wraps has no Langfuse references of
  its own.

## One entry point shared by every caller

Every way an eval actually gets run converges on the same function call:

```
python run_eval.py --component generation ─┐
benchmark.py --evals generation / --quick  ├──▶ evaluate_component(...)
themefinder-eval.yml (CI)                  ─┤              │
future dvc.yaml                            ─┘              ▼
                                              resolve_backends(...) ──▶ run_component(...)
```

`run_eval.py` exposes `evaluate_component(...)` and a CLI that calls it. `benchmark.py` calls the same API, and
the CI workflow reaches it through the benchmark Make targets. No caller owns a separate Langfuse-versus-local
branch. Component factories create the task and evaluator configuration; `evaluate_component(...)` alone
resolves the selected backends and delegates to `run_component(...)`.

### Adding a new eval component

Extending the framework means adding a component module with a task and `ComponentConfig` factory, then
registering it in `components/registry.py`. Component names are derived from the registry keys; datasets,
benchmark argument parsing, and the CLI use those names, while a test keeps the CI workflow choices aligned.
The future DVC parameter list must derive from or be validated against the same registry.

## Architecture overview

Four ports, each an explicit `abc.ABC`, each with a default adapter:

| Port | Role | Default adapter |
|---|---|---|
| `DatasetPort` | Load `list[Case]` for a component/dataset | `LangfuseDatasetAdapter` (Langfuse-enabled runs) or `LocalJSONDatasetAdapter` (otherwise) |
| `EvaluatorPort` | Score a case's output | component-selected evaluator adapters in `evals/adapters/evaluators/` |
| `RunnerPort` | Orchestrate task execution + evaluation | `PydanticEvalsRunner`, wrapping `pydantic_evals.Dataset.evaluate` |
| `ArtefactStorePort` | Persist run/case results and scores | `LangfuseArtefactStore` (default), `LocalJSONArtefactStore` (no-Langfuse) |

```mermaid
flowchart TB
    CLI["run_eval.py"] --> API["evaluate_component(...)"]
    BM["benchmark.py"] --> API
    API -->|"① builds a fresh ComponentConfig"| CF["component registry + factory"]
    API -->|"② calls"| RB["resolve_backends()"]
    RB -->|"③ builds one adapter<br/>per port, bundles them"| EB
    API -->|"④ calls, passing config + backends"| RS["run_component(...)"]
    RS -->|"⑤ reads backends.*"| EB

    EB["EvalBackends<br/>— a plain struct, not a port —<br/>bundles a dataset port,<br/>a runner port, and an<br/>artefact-store port"]

    EB -->|".dataset"| DP["DatasetPort"]
    EB -->|".runner"| RP["RunnerPort"]
    EB -->|".artefacts"| AP["ArtefactStorePort"]
    RP -->|"invokes, per case"| EP["EvaluatorPort"]

    DP -.->|"implemented by"| LDA["LangfuseDatasetAdapter"]
    DP -.->|"implemented by"| LJDA["LocalJSONDatasetAdapter"]

    EP -.->|"implemented by"| CEA["GroundednessEvaluator, etc.<br/>(7 custom evaluators)"]
    EP -.->|"implemented by"| PEA["PydanticEvalsEvaluator<br/>wraps any native Evaluator — built, not wired yet"]

    RP -.->|"implemented by"| PER["PydanticEvalsRunner<br/>default, via THEMEFINDER_EVAL_ENGINE"]
    RP -.->|"implemented by"| ISR["InlineSequentialRunner<br/>test-only"]

    AP -.->|"implemented by"| LAS["LangfuseArtefactStore"]
    AP -.->|"implemented by"| LJAS["LocalJSONArtefactStore"]

    classDef langfuse fill:#f8b4b4,stroke:#902020,color:#1a1a1a
    classDef local fill:#b4d4f8,stroke:#204090,color:#1a1a1a
    classDef pyd fill:#ddc4f8,stroke:#502090,color:#1a1a1a
    classDef port fill:#eee,stroke:#666,color:#1a1a1a,font-weight:bold,stroke-width:2px
    classDef backends fill:#fff3c4,stroke:#8a6d00,color:#1a1a1a,font-weight:bold
    class LDA,LAS langfuse
    class LJDA,LJAS,ISR local
    class PER,PEA pyd
    class CEA local
    class DP,EP,RP,AP port
    class EB backends
```

`EvalBackends` isn't a port and doesn't implement anything — it's the plain struct `resolve_backends()`
returns and `run_component()` reads, holding exactly one concrete adapter per port and nothing else (see
[Orchestration](#orchestration) below for why it doesn't also carry Langfuse's flush-ownership flag). The
grey nodes are the four ports, each an `abc.ABC`; the dashed `implemented by`
arrows below each one are the inheritance relationship called out above — every concrete adapter genuinely
subclasses its port's ABC, `isinstance(adapter, DatasetPort)` holds, and instantiating an adapter missing an
abstract method raises `TypeError`. `RunnerPort` additionally invokes `EvaluatorPort` once per case while
it runs — the one edge between two ports directly, reflecting that the runner is what drives evaluation, not
`run_component()` calling evaluators itself.

Colour key: pink = Langfuse-specific, blue = local/generic, purple = pydantic-evals-specific, grey = a port
(`abc.ABC`), yellow = `EvalBackends`. Every port has at least one adapter of each flavour except
`RunnerPort`, whose only *production* adapter (`PydanticEvalsRunner`) is pydantic-evals-specific by
design — `InlineSequentialRunner` exists purely to prove the port is swappable, not as a real alternative
engine.

`context` is deliberately untyped (`Any`) at the API boundary. `evaluate_component(...)` forwards it to
`resolve_backends` without inspecting it. The
runtime call sequence itself — `resolve_backends()` building `EvalBackends`, `run_component()` reading it — is
covered in full in [Orchestration](#orchestration) below, not repeated here.

## Directory structure

One folder per port, each holding an explicit `abc.ABC` base class in `base.py` and one concrete adapter per
file:

```
evals/adapters/
  __init__.py
  datasets/
    __init__.py
    base.py                  # DatasetPort(ABC) — load_cases(config) -> list[Case]
    langfuse_adapter.py        # LangfuseDatasetAdapter (raises DatasetNotFoundError if the dataset is
                                 # missing or inaccessible — no fallback)
    local_json_adapter.py       # LocalJSONDatasetAdapter
  evaluators/
    __init__.py
    base.py                  # EvaluatorPort(ABC) — async evaluate(case, output) -> list[Score]
    llm_judge_evaluator.py     # shared LLM-judge helpers + LLMJudgeEvaluator(EvaluatorPort), a thin base
                                # the 5 LLM-judge evaluators below subclass for retry/parsing plumbing
    groundedness_evaluator.py   # GroundednessEvaluator(LLMJudgeEvaluator)
    coverage_evaluator.py        # CoverageEvaluator(LLMJudgeEvaluator)
    title_specificity_evaluator.py  # TitleSpecificityEvaluator(LLMJudgeEvaluator)
    condensation_quality_evaluator.py  # CondensationQualityEvaluator(LLMJudgeEvaluator)
    refinement_quality_evaluator.py    # RefinementQualityEvaluator(LLMJudgeEvaluator)
    mapping_f1_evaluator.py             # MappingF1Evaluator(EvaluatorPort) — deterministic, not an LLM judge
    mapping_metrics_evaluator.py        # Preserves the existing mapping metric suite through EvaluatorPort
    redundancy_evaluator.py              # RedundancyEvaluator(EvaluatorPort) — embedding-based, not an LLM judge
    pydantic_evals_evaluator.py  # PydanticEvalsEvaluator, wraps any native pydantic_evals.evaluators.Evaluator
                                    # (e.g. LLMJudge) — built + tested, not wired into any ComponentConfig yet
  runners/
    __init__.py
    base.py                  # RunnerPort(ABC) — async run(config, cases, *, llm) -> RunReport
    inline_sequential_runner.py  # InlineSequentialRunner — no native engine, test-only
    pydantic_evals_runner.py   # PydanticEvalsRunner, wraps pydantic_evals.Dataset.evaluate
  artefact_stores/
    __init__.py
    base.py                  # ArtefactStorePort(ABC) — start_run/record_case/finish_run
    langfuse_adapter.py        # LangfuseArtefactStore
    local_json_adapter.py       # LocalJSONArtefactStore
```

No adapter file imports from a sibling adapter file — each implementation depends only on its own `base.py`.
Filenames use an explicit `_adapter.py` suffix (rather than e.g. `langfuse.py`) so nothing in this tree
shadows the real third-party `langfuse` / `pydantic_evals` packages by name.

`eval_types.py` (shared domain dataclasses), `component_runner.py`, and `config.py` are orchestration, not
themselves adapters, and stay at the top level of `evals/`.

Component-specific code lives separately from adapters:

```
evals/
  components/                # task + ComponentConfig factory per component, plus registry
  run_eval.py                # evaluate_component(...) API and unified CLI
```

### Evaluator adapters and utility modules

Framework evaluators are one `EvaluatorPort` subclass per file under `evals/adapters/evaluators/`.
`ComponentConfig.evaluators` holds fresh instances with the judge LLM bound wherever needed. The legacy
`evaluators.py` remains for the existing mapping DVC prototype and other compatibility callers; it is not
used by the unified component path. `metrics.py` is also retained, with `MappingMetricsEvaluator` adapting
its established mapping metric calculation to the evaluator port.

**`evals/utils/`** replaces the flat `evals/langfuse_utils.py` and the unrelated `evals/utils.py`:

```
evals/utils/
  __init__.py
  langfuse.py                   # Langfuse context, tracing, flush, and metrics helpers
                                 # flush, extract_session_metrics, ...)
  prompt_utils.py                # moved verbatim from evals/utils.py (read_and_render) — renamed only
                                  # because a `utils.py` module and a `utils/` package can't coexist at the
                                  # same directory level; nothing in evals/ imports read_and_render today
```

`benchmark.py` and `generate_synthetic.py` continue to import the Langfuse helper module because they
legitimately manage tracing. Component definitions and the unified API/CLI do not import it.

## Domain types — `evals/eval_types.py`

Framework-owned types, so no port implementation needs to import `pydantic_evals` or `langfuse` types
directly. A handful of small, frozen dataclasses — `Case`, `Score`, `CaseOutcome`, `RunReport`, and
`ComponentConfig` — plus a `DatasetNotFoundError` exception that a `DatasetPort` raises and
`FallbackDatasetAdapter` catches to trigger its fallback. `Score` is isomorphic to today's `{"name",
"value", "comment"}` shape, so converting `evaluators.py` output is a one-liner.

`ComponentConfig.task` takes `case.inputs` — a plain `dict` — not the full `Case` object. This is deliberate: it
matches pydantic-evals' native task contract, since its evaluation loop invokes a task with just a case's
inputs, so `PydanticEvalsRunner` needs no bridging on the task side. `run_component` binds the LLM once before
handing the resulting callable to whichever runner is active. If a component genuinely needs data from
`Case.metadata` inside its task, that data is folded into `inputs` when the dataset adapter builds the
`Case`, rather than widening this contract back to the full `Case`.

## Ports

Each port is an `abc.ABC` living in its own `base.py`, with a single narrow responsibility matching its row
in the table above — `DatasetPort` loads cases, `EvaluatorPort` scores a case, `RunnerPort` orchestrates
execution, `ArtefactStorePort` starts/records/finishes a run.

Every concrete adapter — `LangfuseDatasetAdapter`, `LocalJSONDatasetAdapter`, the evaluator classes in
`evals/adapters/evaluators/`, `PydanticEvalsEvaluator`, `PydanticEvalsRunner`, `LangfuseArtefactStore`,
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
  and stamps `Case.metadata["langfuse_item_id"] = item.id` on every `Case` it builds. This is the *only*
  channel the Langfuse dataset item ID crosses into the artefact store — not a direct reference to the
  adapter instance, which would violate "no adapter file imports from a sibling adapter file."
  `LocalJSONDatasetAdapter`-sourced cases simply never carry this key. If `client.get_dataset(...)` fails —
  the dataset doesn't exist, or credentials lack access — it raises `DatasetNotFoundError` and lets it
  propagate; there is no fallback. If Langfuse is the configured dataset source, a missing or inaccessible
  dataset is a real error to surface, not something to silently substitute a local fixture for.
- **`LocalJSONDatasetAdapter`** loads cases from `evals/data/<dataset>/`, building on the
  Langfuse-vs-local-JSON duality already present in `datasets.py::load_local_data`.

### Evaluator adapters

The framework evaluators are direct `EvaluatorPort` subclasses in
`evals/adapters/evaluators/`, each producing `list[Score]` from its own `evaluate(case, output)` — no
generic wrapper, no return-shape normalisation step, since each class owns its own conversion from whatever
its LLM call returns straight into `Score`.

Five evaluator adapters (`GroundednessEvaluator`, `CoverageEvaluator`, `TitleSpecificityEvaluator`,
`CondensationQualityEvaluator`, `RefinementQualityEvaluator`) are LLM judges and share a common base,
`LLMJudgeEvaluator(EvaluatorPort)` in `common.py`, which carries the retry logic (`_invoke_with_retry`) and
shared parsing helpers so no individual class re-implements them. `MappingF1Evaluator`,
`MappingMetricsEvaluator` (deterministic mapping metrics), and `RedundancyEvaluator` (embedding similarity)
have no LLM-call plumbing to share, so they subclass `EvaluatorPort` directly instead. Every class's
`evaluate()` is declared `async def` — that is the port's contract — regardless of whether its own body
actually awaits anything.

**`PydanticEvalsEvaluator`** wraps any native `pydantic_evals.evaluators.Evaluator` (e.g. `LLMJudge`) behind
the same `EvaluatorPort`
— the planned home for the team's expected future migration of the five custom LLM-judge classes onto
pydantic-evals' own judge primitive, per ADR-0011's "use pydantic-evals for LAJ" mandate. Built and
unit-tested this pass (stubbed `LLMJudge`, no network); not wired into any `ComponentConfig` yet — retiring a
custom evaluator class is an output-quality-parity judgment call for a dedicated future pass, not a
side effect of this one.

(Confidence flag, structural not just naming: the above assumes `EvaluatorContext` can be constructed
standalone, outside pydantic-evals' own `Dataset.evaluate()` loop — not verified this session.
`EvaluatorContext` may carry fields the engine populates internally during a real run (span/trace data,
attempt counts, or similar) that aren't reproducible from just `Case` + `output`, in which case
`LLMJudge.evaluate(ctx)` could fail or behave differently against a hand-built `ctx`. **First implementation
step: a standalone spike confirming `EvaluatorContext(...)` can be built and passed to `LLMJudge.evaluate()`
outside `Dataset.evaluate()` at all**, before writing the rest of the adapter around that assumption. If it
can't, the adapter's shape needs to change — most likely to only support native pydantic-evals evaluators
when `PydanticEvalsRunner` is actually driving the full `Dataset.evaluate()` call, a real constraint on the
"any evaluator, any runner" swappability claim, not just an implementation detail.

Resolved: the spike was done — `EvaluatorContext` builds standalone with no missing fields, confirmed by a
real passing test, `test_pydantic_evals_evaluator.py::test_wraps_real_llm_judge`.)

This has to go through `EvaluatorPort`, not bypass it. The shortcut of handing `LLMJudge` instances straight
to `pydantic_evals.Dataset(evaluators=[...])` inside `PydanticEvalsRunner` only works while `PydanticEvalsRunner`
is the active runner — the moment a `ComponentConfig` mixes a bypassed-native evaluator with any other runner
(`InlineSequentialRunner` included), that evaluator silently can't run, breaking the swappability the whole
framework is built around for that one evaluator. Wrapping it costs one adapter file and keeps every
evaluator — native or custom — runnable under every runner. The migration path this unlocks:
`ComponentConfig.evaluators` is a plain `list[EvaluatorPort]`, and nothing stops that list from mixing adapter
types — `groundedness` could move to `PydanticEvalsEvaluator` while `coverage` stays on
`CoverageEvaluator`, one evaluator at a time, with zero change to `run_component`, either runner, or any
artefact store.

### Runner adapter

**`PydanticEvalsRunner`** wraps `pydantic_evals.Dataset.evaluate`. Internally it builds a
`pydantic_evals.Dataset(cases=[...], evaluators=[...])`, wrapping each `config.evaluators` entry individually
(not fanning a single bridge out over the whole list): every entry is wrapped one-for-one in
`_EvaluatorPortAsNativeEvaluator(port=...)`, which translates the port's `list[Score]` back into
pydantic-evals' expected return shape. A `PydanticEvalsEvaluator` is handed the real native
`EvaluatorContext` through `evaluate_in_context(ctx)` (real tracing, no round-trip through a reconstructed
context), while still passing through `EvaluatorPort`'s shared error boundary and metric-name projection, so
a failing evaluator degrades to zero scores exactly as under `InlineSequentialRunner`; any other port gets a
framework `Case` rebuilt from the context (`.inputs`, `.output`, `.expected_output`, `.metadata`, `.name`)
and is called through `evaluate()`. `Dataset.evaluate(task, max_concurrency=...)`
is then called once per run, not per evaluator. It also populates `RunReport.engine_report` with the native
`EvaluationReport` object `Dataset.evaluate()` returns — see [Surfacing pydantic-evals' native
EvaluationReport](#surfacing-pydantic-evals-native-evaluationreport-without-widening-the-ports)
below. Every other runner (`InlineSequentialRunner` included) leaves `engine_report` at its default, `None`.

### Artefact store adapters

- **`LangfuseArtefactStore`** mirrors the trace/score-pushing logic currently duplicated in every
  `_run_with_langfuse`. Its constructor takes the context and whether it owns it, capturing the
  flush-ownership decision at construction time rather than on any shared struct (see
  [Orchestration](#orchestration) below for why); `finish_run()` flushes only when it owns the context, so a
  context supplied by a caller like `benchmark.py` is never flushed twice. It's also the only adapter that
  unpacks `engine_report` when `finish_run()` receives one.
  `record_case()` looks for a Langfuse item id on the case's metadata defensively: present, it links the
  score to that Langfuse dataset item exactly as `_run_with_langfuse` does today; absent, it still creates a
  trace and pushes scores, just without dataset-item linkage, instead of crashing. This isn't a fallback
  degradation path — dataset source and artefact store are two independent choices (see
  [Orchestration](#orchestration) below), so "Langfuse artefact store, locally-sourced case" is a normal,
  deliberately-supported combination (someone who wants results stored locally while still pulling cases
  from a curated Langfuse dataset), not an edge case.
- **`LocalJSONArtefactStore`** writes to `evals/local_eval_runs/<component>/<dataset>/results.json`, overwritten
  each run — deliberately not `evals/benchmark_results/`, which `benchmark.py` already owns as a
  timestamp-keyed directory (`benchmark_results/<benchmark_id>/benchmark.log`) that `visualise_benchmark.py`
  scans expecting only timestamp children. `local_eval_runs/` is a strict improvement over today's local
  fallback, which never persisted anything at all — but it's a separate, non-interchangeable output tree from
  `benchmark.py`'s results directory. `visualise_benchmark.py` only reads persisted
  Langfuse/`benchmark_results` data and is not updated to read `local_eval_runs/` in this pass. The future DVC
  work will decide how the unified CLI guarantees this stable output when another artefact store is selected.

Both return the same flat `dict[str, Any]` shape `benchmark.py` already parses (see below).

### Surfacing pydantic-evals' native `EvaluationReport` without widening the ports

`RunReport.engine_report` is how `PydanticEvalsRunner`'s native `EvaluationReport` reaches
`LangfuseArtefactStore` without breaking swappability — worth spelling out exactly why this doesn't
compromise the port design, since it's the one place a runner-specific object crosses an adapter boundary:

`ArtefactStorePort.finish_run` gains one optional, keyword-only, `Any`-typed parameter — no `pydantic_evals`
import anywhere near the ABCs, and every adapter but `LangfuseArtefactStore` just ignores it (`PydanticEvalsRunner`
populates it, every other runner leaves it `None`). `LangfuseArtefactStore` is the only place that unpacks it,
and does so behind an `isinstance(engine_report, pydantic_evals.reporting.EvaluationReport)` check rather than
a bare truthiness check, since `engine_report` being `Any` means a future second engine could populate it with
something else entirely. The swappability test proves this stays additive, not load-bearing: it asserts
`engine_report is None` for `InlineSequentialRunner` and not for `PydanticEvalsRunner`, alongside an identical
`outcomes`/`scores` comparison either way.

**What `LangfuseArtefactStore` does with it, this pass:** call `engine_report.print()` (or equivalent) for a
richer console summary at the end of a run, and/or pull per-case timing data pydantic-evals already tracks
into the score dict as extra metadata — both safe, mechanical wins with the shape verified above.

**Real follow-up, not this pass:** whether pydantic-evals' own OpenTelemetry instrumentation (if `Dataset.
evaluate()` emits per-case/per-evaluator spans) can feed Langfuse more directly than the current custom
`dataset_item_trace`/`ctx.client.create_score(...)` bookkeeping. That's a materially bigger change — it would
touch how traces get *created*, not just how the final summary gets built — and its feasibility depends on
exact `pydantic-evals`/Langfuse SDK version behaviour not verified in this pass. Worth a dedicated spike
before committing to it.

## Orchestration

### `evals/config.py::resolve_backends`

`resolve_backends` returns an `EvalBackends` bundle with deliberately just three fields, one per port: the
resolved dataset, runner, and artefact store. The Langfuse flush-ownership decision lives inside
`LangfuseArtefactStore`, not on this shared struct. `resolve_backends` passes `owns_context=True` when it
constructed the context itself and `False` for a caller-supplied context, ensuring the latter is not flushed
twice.

This is the **only** orchestration function anywhere that touches `langfuse_utils` / `LangfuseContext`
directly (besides the Langfuse adapter modules themselves), and it does so lazily, in this order:

1. **Resolve `dataset_source` and `artefact_store` first, from settings alone** — no context construction
   needed yet. Each is selected explicitly through `EvalSettings.eval.dataset_source` /
   `.artefact_store`, populated from `THEMEFINDER_EVAL_DATASET_SOURCE` /
   `THEMEFINDER_EVAL_ARTEFACT_STORE`, and defaults to `"local"` when unset. Requesting `"langfuse"` for
   either without the required secret key, public key, and base URL is a hard error right here — asking for
   a backend you have no way to reach isn't a case to degrade gracefully from. This is what lets someone
   deliberately run `dataset=langfuse, artefacts=local` (pull cases from a curated Langfuse dataset, keep
   results local) or the reverse, without either choice silently dragging the other along with it.
2. **Only if at least one of the two resolved to `"langfuse"`**, build the context — using the one the
   caller supplied if there is one, otherwise constructing a default one via `get_langfuse_context` — and
   remember in a local variable whether it owns this context (i.e. none was supplied). A fully local run
   (`dataset_source == artefact_store == "local"`) never calls `get_langfuse_context()` at all.
3. Construct whichever adapters were resolved: a `"langfuse"` choice gets the Langfuse dataset or artefact
   adapter, with the artefact adapter also told whether it owns the context from step 2; a `"local"` choice
   gets the local-JSON equivalent. That ownership flag is consumed directly by the Langfuse artefact
   adapter's own construction and never reaches the `EvalBackends` returned.

It picks the runner via one environment variable, `THEMEFINDER_EVAL_ENGINE` (default `pydantic_evals`),
read once at the top of the function — the explicit seam a second engine plugs into later. There is no
plugin registry; this is deliberately simple, the same pattern the two new selectors above follow.

### `evals/component_runner.py::run_component`

`run_component` loads cases via `backends.dataset`, reads pre-built evaluators from `ComponentConfig.evaluators`, runs
the task via `backends.runner`, records and finishes via `backends.artefacts`, and returns a flat result
dict. Pure ports — no `langfuse` or `pydantic_evals` import, no conditional branching on context state. This is
the function the unified evaluation API delegates to and the function the swappability test exercises directly
with fake backends.

### Component definitions and unified API

Each module under `evals/components/` defines one async task and one `ComponentConfig` factory. The registry
selects the factory, and `evaluate_component(...)` creates a fresh configuration for every invocation before
resolving backends and calling `run_component()`. Fresh construction matters because LLM-judge evaluators bind
the judge LLM at construction time and mapping's optional question filter is invocation-specific.

`run_eval.py` provides the single-component CLI. Mapping keeps its optional `--question` flag, implemented as
a per-call `case_filter`; it applies equally to local and Langfuse dataset adapters. `benchmark.py` calls
`evaluate_component(...)` directly rather than maintaining a second component-to-function mapping.

**Scoring-consistency status per component:** generation, condensation, and refinement are already consistent —
each already calls the same `evaluators.py` LLM-judge suite in both its local and Langfuse paths, so this
plan does not change their scoring. Mapping now uses `MappingMetricsEvaluator` for both dataset sources. That
adapter delegates to `metrics.py::calculate_mapping_metrics`, preserving F1, exact-match accuracy, overlap
rate, and the F1 confidence interval instead of narrowing mapping to F1 alone.

## Running via DVC

A fourth caller of `evaluate_component()`, alongside direct CLI, `benchmark.py`, and the CI workflow —
`evals/dvc.yaml` defines pipeline stages that shell out to `run_eval.py --component <name>`, never
`run_component()` directly. This buys `dvc repro`'s dependency-aware caching (skip re-running a component when
nothing it depends on has changed) and `dvc exp run`/`dvc metrics show` for comparing intentional variations
as tracked experiments — not strict reproducibility, since LLM evals are stochastic, but a real win for
"nothing relevant changed, don't bother re-running" and for comparing designed variations.

Full `dvc.yaml`/`params.yaml` listing lives in the working plan's "Running via DVC" section, not duplicated
here. One point worth calling out at this level: DVC needs a concrete local `metrics` file to track for
every component, but `LangfuseArtefactStore` does not write anything to disk. The DVC implementation therefore
adds a stable CLI-level metrics output independently of the configured artefact store. This remains a DVC
concern: `run_component()` and `ArtefactStorePort` stay unchanged.

## Compatibility contract with benchmark.py

`benchmark.py` calls `evaluate_component()` with the component name, dataset, LLM, context, and optional judge
LLM. It expects a flat dict back, which it splits by value type into `scores` vs `outputs`. It also owns opening
the Langfuse trace context itself and later calls
`langfuse_utils.extract_session_metrics(session_id=...)` for cost/token data.

The generic API preserves this return shape and accepts the caller-owned context through an untyped `context`
parameter. This keeps component definitions storage-agnostic without changing how `benchmark.py` itself talks
to Langfuse.

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

Pre-migration inventory:

| Env var | Read independently in | Call sites |
|---|---|---|
| `AUTO_EVAL_MODEL` (prev `AUTO_EVAL_4_1_SWEDEN_DEPLOYMENT`) | `eval_generation.py`, `eval_condensation.py`, `eval_mapping.py`, `eval_refinement.py`, `langfuse_utils.py` | 5 |
| `LANGFUSE_SECRET_KEY` / `PUBLIC_KEY` / `BASE_URL` | `langfuse_utils.py`, `benchmark.py::query_langfuse_costs()` (builds its own `Langfuse` client from a second, independent read) | 2 |
| `LANGFUSE_BASE_URL` / `LANGFUSE_PROJECT_ID` | `visualise_benchmark.py` | adds a 3rd site for `LANGFUSE_BASE_URL` |
| `LLM_GATEWAY_URL` / `CONSULT_EVAL_LITELLM_API_KEY` | `utils_gateway.py` | 1 (already fine) |
| `ENVIRONMENT`, `GITHUB_SHA` | `langfuse_utils.py` | 1 (already fine) |
| `THEMEFINDER_EVAL_ENGINE` (new) | `config.py::resolve_backends` | 1 (new, single-sited by construction) |
| `THEMEFINDER_EVAL_DATASET_SOURCE` (new) | `config.py::resolve_backends` | 1 (new, single-sited by construction; see [Orchestration](#orchestration)) |
| `THEMEFINDER_EVAL_ARTEFACT_STORE` (new) | `config.py::resolve_backends` | 1 (new, single-sited by construction; see [Orchestration](#orchestration)) |

Before the component migration, `dotenv.load_dotenv()` was called independently in 7 files (`benchmark.py`, all four `eval_*.py`,
`visualise_benchmark.py`, `generate_synthetic.py`) — the same "everyone re-does the same setup" problem one
level up.

### `evals/settings.py`

A new module (deliberately not `config.py`, which already names the module that wires adapters together)
holding one frozen dataclass, `EvalSettings`, that bundles every value the eval suite currently reads from
the environment independently: the LLM/gateway credentials, the Langfuse credentials and project ID,
`ENVIRONMENT`/`GITHUB_SHA`, and the three eval-specific switches (`eval_engine`, `eval_dataset_source`,
`eval_artefact_store` — the latter two defaulting to `None`, i.e. defer to `resolve_backends`' own
credential-based default). A single `get_settings()` function, cached as a process-wide singleton, loads
`.env` and reads every environment variable exactly once, however many modules call it; being frozen, nothing
can mutate the result afterwards.

**Dependency injection lands exactly at the boundaries that already have one** — `resolve_backends` and the
two existing shared helper functions (`get_langfuse_context`, `gateway_credentials`) each grow an optional
settings parameter, defaulting to `get_settings()`, the same optional-with-a-default pattern `context`
already uses; no existing call site changes. `get_settings()` then replaces every other scattered read this
pass found — `query_langfuse_costs()`'s and `visualise_benchmark.py`'s independent credential reads, the
five inline per-component `os.getenv("AUTO_EVAL_MODEL")` sites, and all seven explicit `dotenv.load_dotenv()`
calls (deleted outright, since `get_settings()` already guarantees `.env` is loaded before any field is
read).

This keeps component definitions and the unified API/CLI free of Langfuse-specific code. `EvalSettings`
bundles Langfuse fields alongside non-Langfuse ones, but component definitions never inspect them.

### Test impact: a real correctness risk, not just style

`test_benchmark.py` and `test_utils_gateway.py` already have 12 `monkeypatch.setenv(...)` calls between them.
A naive `@lru_cache` singleton would silently break both: the first test to call `get_settings()` poisons the
cache for every later test expecting a different env var value, since `lru_cache` never re-reads after the
first call. This needs an autouse fixture in `evals/tests/conftest.py` that clears the cache before and
after every test, so the existing `monkeypatch.setenv` usage keeps working with zero changes to
`test_benchmark.py` or `test_utils_gateway.py` themselves.

## Rollout sequencing

This work is broken down into 8 issues across five waves:

- **Wave 0 — Groundwork** (1 issue, lots of small changes): extras group (including `dvc`), `eval_types.py`,
  `settings.py` + its test fixture, the `utils/` directory move, wiring `settings.py` into existing helpers.
  All additive or mechanical — nothing production-facing changes yet. There's no separate
  `evaluators.py`-split issue here, since retiring it happens directly inside the `EvaluatorPort` issue below.
- **Wave 1 — Ports** (4 issues, parallelisable): one issue per port type — `DatasetPort`, `EvaluatorPort` (all seven evaluator classes plus `PydanticEvalsEvaluator`), `RunnerPort`, `ArtefactStorePort` — each self-contained with its own offline tests. None of them are wired into production code yet, so a team can split these across people. The `EvaluatorPort` issue's first step is the `EvaluatorContext`-standalone-construction spike flagged under [Evaluator adapters](#evaluator-adapters) above — if it fails, `PydanticEvalsEvaluator` splits off into its own follow-up issue and this one narrows to the seven custom classes.
- **Wave 2 — Orchestration** (1 issue): `resolve_backends` + `run_component` + the swappability proof. The
  architecture's proof point — every port comes together here for the first time.
- **Wave 3 — Component migrations** (1 issue): move all four component tasks and evaluator configurations into
  `evals/components/`, add the `evaluate_component(...)` API and `run_eval.py` CLI, migrate `benchmark.py`,
  then remove only the four legacy `eval_*.py` scripts. The compatibility modules and mapping DVC prototype
  remain in place.
- **Wave 4 — DVC pipeline** (1 issue): `evals/dvc.yaml` + `evals/params.yaml` (see [Running via
  DVC](#running-via-dvc) above). Independent of the ports-and-adapters refactor — it only shells out to the
  unified `run_eval.py` entry point. `params.yaml` must be generated from or validated against
  the component registry rather than becoming another independent list of component names.

Every issue in every wave leaves `pytest tests/` and `pytest evals/tests/` green — none of them is a partial
or broken intermediate state.

## Testing strategy

- `evals/tests/fakes.py` provides `FakeDatasetPort`, `FakeEvaluatorPort`, `FakeArtefactStore` (each
  subclassing the real ABC) and `InlineSequentialRunner` — a ~15-line loop implementing `RunnerPort` with
  zero pydantic-evals dependency.
- **Swappability proof** (`test_component_runner.py`): the same fake cases, evaluators, and task run once through
  `PydanticEvalsRunner()` and once through `InlineSequentialRunner()`, asserting identical `RunReport.
  outcomes`/`scores` — the one expected difference, `engine_report` (populated for `PydanticEvalsRunner`,
  `None` otherwise), is asserted explicitly rather than silently ignored. This is the concrete evidence the
  abstraction isn't paper-thin — it's what would catch any accidental coupling of evaluator, dataset, or
  artefact logic to pydantic-evals internals.
- **LAJ adapter proof** (`test_evaluator_adapters.py`): `PydanticEvalsEvaluator`, built against a
  stubbed `LLMJudge`, passes the same ABC-subclass checks as every other evaluator class, and its
  `evaluate()` output matches the `list[Score]` shape a custom evaluator like `GroundednessEvaluator`
  produces — proving a native pydantic-evals judge and a custom one are genuinely interchangeable in a
  `ComponentConfig.evaluators` list.
- **Dataset-source failure / independent-selection proof** (`test_dataset_adapters.py`, `test_config.py`,
  `test_artefact_store.py`): a `LangfuseDatasetAdapter` pointed at a nonexistent dataset name raises
  `DatasetNotFoundError` rather than falling back to anything; `resolve_backends()` wires `dataset=langfuse,
  artefacts=local` and `dataset=local, artefacts=langfuse` correctly from `THEMEFINDER_EVAL_DATASET_SOURCE`
  / `THEMEFINDER_EVAL_ARTEFACT_STORE`, and raises when either explicitly requests `"langfuse"` without
  Langfuse credentials configured; separately, `LangfuseArtefactStore.record_case()` called with a `CaseOutcome` whose
  case lacks `"langfuse_item_id"` (the `dataset=local, artefacts=langfuse` combination) creates a trace and
  pushes scores without raising, just without dataset-item linkage.
- Each adapter has its own offline unit test (`test_dataset_adapters.py`, `test_evaluator_adapters.py`,
  `test_artefact_store.py`), each asserting the concrete adapter is a genuine subclass of its ABC and that
  instantiating an incomplete subclass raises `TypeError`.
- A grep-based check enforces the zero-Langfuse-in-component-code rule directly:
  `grep -ril langfuse evals/components evals/run_eval.py evals/component_runner.py evals/eval_types.py evals/adapters/*/base.py
  evals/adapters/evaluators/*.py` must return nothing, aside from `pydantic_evals_evaluator.py`
  (which legitimately imports `pydantic_evals`, not `langfuse` — the grep target is `langfuse`, not
  `pydantic_evals`, so this file is expected to be clean too).
- A second grep-based check enforces the `os.getenv()` centralisation directly: `grep -rn "os\.getenv\|os\.
  environ\.get" evals/*.py` returns only one line per var inside `evals/settings.py::get_settings()`, plus
  `benchmark.py`'s unrelated `GRPC_DNS_RESOLVER` process-level workaround (not app config, not migrated).
  `grep -rn load_dotenv evals/*.py` returns only `evals/settings.py` after the legacy scripts are removed.
- `langfuse_utils.py`'s split is checked for byte-level fidelity: its content is diffed against
  `git show HEAD:themefinder/evals/langfuse_utils.py` to confirm relocation only, no rewriting.
  Component tests exercise all four task output schemas, evaluator selection, fresh configuration construction,
  and exact mapping question filtering. `evaluators.py` and `metrics.py` remain available for compatibility.
- `pytest tests/ -v` (95% coverage gate) and `pytest evals/tests/ -v` — including the untouched
  `test_benchmark.py` and `test_utils_gateway.py`, whose 12 `monkeypatch.setenv` calls keep passing via the
  new autouse cache-clearing fixture — stay green throughout every phase.

## Deferred to a later pass

- Removing `benchmark.py`'s remaining *direct* Langfuse coupling (context construction, flush, and
  cost/token metrics extraction) by routing it through `resolve_backends`/`ArtefactStorePort` instead — the
  minimal-change design for this is written up in the "Follow-up (deferred)" section of the working plan, not
  duplicated here.
- Removing `generate_synthetic.py`'s equivalent direct Langfuse coupling (its own `LangfuseContext`
  construction, trace wrap, and flush — pure LLM-call tracing, not dataset storage; it never writes to a
  Langfuse dataset). Structurally similar to `benchmark.py`'s coupling but smaller, and tracked as its own
  separate follow-up issue rather than folded into the `benchmark.py` write-up, since the two scripts have no
  shared call path.
- Actually migrating any of the five custom LLM-judge classes onto `PydanticEvalsEvaluator` —
  the adapter exists and is tested this pass, but retiring a custom judge is an output-quality-parity
  decision, not a mechanical one.
- Investigating whether pydantic-evals' native OpenTelemetry instrumentation can feed Langfuse traces more
  directly than the current custom `dataset_item_trace`/`ctx.client.create_score(...)` bookkeeping —
  a bigger change than the `engine_report` escape hatch, not verified against actual SDK behaviour this pass.
