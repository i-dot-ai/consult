"""Build the dataset, runner and artefact store selected by eval settings."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from adapters.artefact_stores import (
    ArtefactStorePort,
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
from adapters.runners.pydantic_evals_runner import PydanticEvalsRunner
from datasets import DatasetConfig
from settings import EvalSettings, get_settings
from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class EvalBackends:
    """Adapter instances for one evaluation run, built from the current settings."""

    dataset: DatasetPort
    runner: RunnerPort
    artefacts: ArtefactStorePort
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
RunnerFactory = Callable[[], RunnerPort]


def _local_dataset_factory(context: Any | None) -> DatasetPort:
    del context
    return LocalJSONDatasetAdapter()


def _langfuse_dataset_factory(context: Any | None) -> DatasetPort:
    return LangfuseDatasetAdapter(context.client)


def _local_artefact_factory(context: Any | None) -> ArtefactStorePort:
    del context
    return LocalJSONArtefactStore()


def _langfuse_artefact_factory(context: Any | None) -> ArtefactStorePort:
    return LangfuseArtefactStore(context)


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
}


def resolve_backends(
    dataset_config: DatasetConfig,
    *,
    settings: EvalSettings | None = None,
    context: dict[str, Any] | None = None,
) -> EvalBackends:
    """Resolve each backend independently, defaulting to local storage.

    Each platform a source needs gets one context, shared by the sources that
    use it. ``context`` maps platform name to a caller-supplied context, which
    stays the caller's responsibility to flush; contexts created here are
    released by ``EvalBackends.close()``.
    """

    settings = settings if settings is not None else get_settings()
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
    return EvalBackends(
        dataset=DATASET_FACTORIES[dataset_source](dataset_context),
        runner=RUNNER_FACTORIES[settings.eval.engine](),
        artefacts=ARTEFACT_FACTORIES[artefact_store_source](artefact_context),
        contexts=provided,
    )
