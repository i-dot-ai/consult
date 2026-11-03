"""Build the dataset, runner and artefact store selected by eval settings."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from adapters.artefact_stores import (
    ArtefactStorePort,
    CompositeArtefactStore,
    LangfuseArtefactStore,
    LocalJSONArtefactStore,
)
from adapters.context_providers import CONTEXT_PROVIDERS, ProvidedContext
from adapters.datasets import (
    DatasetPort,
    LangfuseDatasetAdapter,
    LocalJSONDatasetAdapter,
)
from adapters.runners import RunnerPort
from adapters.runners.inline_sequential_runner import InlineSequentialRunner
from adapters.runners.pydantic_evals_runner import PydanticEvalsRunner
from adapters.tracing import TRACER_FACTORIES, NoopTracer, TracerPort
from datasets import DatasetConfig
from settings import EvalSettings, eval_settings
from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class EvalBackends:
    """Adapter instances for one evaluation run, built from the current settings."""

    dataset: DatasetPort
    runner: RunnerPort
    artefacts: ArtefactStorePort
    tracer: TracerPort = field(default_factory=NoopTracer, repr=False)
    contexts: dict[str, ProvidedContext] = field(default_factory=dict, repr=False)

    def close(self) -> None:
        """Release every context we created, even if one release fails."""
        for platform, provided in self.contexts.items():
            try:
                provided.close()
            except Exception:
                logger.exception("Failed to close %s context", platform)


DatasetFactory = Callable[[Any | None], DatasetPort]
ArtefactFactory = Callable[[Any | None], ArtefactStorePort]
RunnerFactory = Callable[..., RunnerPort]  # called as factory(repeat=N)


def _local_dataset_factory(context: Any | None) -> DatasetPort:
    del context
    return LocalJSONDatasetAdapter()


def _langfuse_dataset_factory(context: Any | None) -> DatasetPort:
    return LangfuseDatasetAdapter(context.client)


def _local_artefact_factory(context: Any | None) -> ArtefactStorePort:
    del context
    return LocalJSONArtefactStore()


def _langfuse_artefact_factory(context: Any | None) -> ArtefactStorePort:
    return CompositeArtefactStore(
        LocalJSONArtefactStore(),
        LangfuseArtefactStore(context),
    )


DATASET_FACTORIES: dict[str, DatasetFactory] = {
    "local": _local_dataset_factory,
    "langfuse": _langfuse_dataset_factory,
}
ARTEFACT_FACTORIES: dict[str, ArtefactFactory] = {
    "local": _local_artefact_factory,
    "langfuse": _langfuse_artefact_factory,
}
RUNNER_FACTORIES: dict[str, RunnerFactory] = {
    "pydantic_evals": PydanticEvalsRunner,
    "local": InlineSequentialRunner,
}


def _available_tracing_platform(settings: EvalSettings) -> str | None:
    """The platform to trace on, decided by the credentials present alone."""
    return "langfuse" if settings.active_langfuse is not None else None


def _resolve_tracer(
    settings: EvalSettings, context_for: Callable[[str], Any | None]
) -> TracerPort:
    """Trace on the platform with a connection, or on none when it cannot be reached.

    When neither source uses the platform this creates a context for tracing alone,
    on purpose: the credentials opted the run in, and ``EvalBackends.close()`` flushes it
    with the others.
    """
    platform = _available_tracing_platform(settings)
    if platform is None:
        return NoopTracer()
    try:
        return TRACER_FACTORIES[platform](context_for(platform))
    except ValueError as error:
        # A source that selected the platform has already created and validated this context,
        # so only a run that merely traces on it gets here, and it must go on untraced.
        logger.warning("Tracing on %s is off for this run: %s", platform, error)
        return NoopTracer()


def resolve_backends(
    dataset_config: DatasetConfig,
    *,
    settings: EvalSettings | None = None,
    context: dict[str, Any] | None = None,
    repeat: int = 1,
) -> EvalBackends:
    """Resolve each backend independently, defaulting to local storage.
    Contexts created here are released by ``EvalBackends.close()``.
    ``repeat`` is how many times the runner runs every case. Tracing is on
    whenever a platform has a connection, whatever the two sources are.
    """

    settings = settings if settings is not None else eval_settings
    dataset_source = settings.eval.dataset_source or "local"
    artefact_store_source = settings.eval.artefact_store or "local"
    supplied = context or {}
    provided: dict[str, ProvidedContext] = {}

    def context_for(source: str) -> Any | None:
        """Create a source's context on first use so sources on one platform share it.

        Source names double as platform names: a source with no entry in
        ``CONTEXT_PROVIDERS`` (e.g. ``"local"``) gets ``None``, so a new
        platform-backed source must register a provider under the same name.
        """
        provider = CONTEXT_PROVIDERS.get(source)
        if provider is None:
            return None
        if source not in provided:
            provided[source] = provider(dataset_config, settings, supplied.get(source))
        return provided[source].context

    dataset_context = context_for(dataset_source)
    artefact_context = context_for(artefact_store_source)
    tracer = _resolve_tracer(settings, context_for)
    return EvalBackends(
        dataset=DATASET_FACTORIES[dataset_source](dataset_context),
        runner=RUNNER_FACTORIES[settings.eval.engine](repeat=repeat),
        artefacts=ARTEFACT_FACTORIES[artefact_store_source](artefact_context),
        tracer=tracer,
        contexts=provided,
    )
