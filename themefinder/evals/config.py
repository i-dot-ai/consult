"""Build the dataset, runner and artefact store selected by eval settings."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from adapters.artefact_stores import (
    ArtefactStorePort,
    LangfuseArtefactStore,
    LocalJSONArtefactStore,
)
from adapters.datasets import (
    DatasetPort,
    LangfuseDatasetAdapter,
    LocalJSONDatasetAdapter,
)
from adapters.runners import (
    PydanticEvalsRunner,
    RunnerPort,
)
from datasets import DatasetConfig
from settings import EvalSettings, get_settings


@dataclass(frozen=True)
class EvalBackends:
    """Adapter instances for one evaluation run, built from the current settings."""

    dataset: DatasetPort
    runner: RunnerPort
    artefacts: ArtefactStorePort


DatasetFactory = Callable[[Any | None], DatasetPort]
ArtefactFactory = Callable[[Any | None, bool], ArtefactStorePort]
RunnerFactory = Callable[[], RunnerPort]


def _require_langfuse_context(context: Any | None) -> Any:
    if (
        context is None
        or not getattr(context, "is_enabled", False)
        or getattr(context, "client", None) is None
    ):
        raise ValueError("Langfuse was selected but its context is unavailable.")
    return context


def _local_dataset_factory(context: Any | None) -> DatasetPort:
    del context
    return LocalJSONDatasetAdapter()


def _langfuse_dataset_factory(context: Any | None) -> DatasetPort:
    langfuse_context = _require_langfuse_context(context)
    return LangfuseDatasetAdapter(langfuse_context.client)


def _local_artefact_factory(
    context: Any | None, owns_context: bool
) -> ArtefactStorePort:
    del context, owns_context
    return LocalJSONArtefactStore()


def _langfuse_artefact_factory(
    context: Any | None, owns_context: bool
) -> ArtefactStorePort:
    langfuse_context = _require_langfuse_context(context)
    return LangfuseArtefactStore(langfuse_context, owns_context=owns_context)


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
    context: Any | None = None,
) -> EvalBackends:
    """Resolve each backend independently, defaulting to local storage.

    Langfuse is opt-in. Its adapters share one context, created here only when
    needed. A caller-supplied context remains the caller's responsibility to flush.
    """

    settings = settings if settings is not None else get_settings()
    dataset_source = settings.eval.dataset_source or "local"
    artefact_store_source = settings.eval.artefact_store or "local"
    owns_context = False

    if "langfuse" in (dataset_source, artefact_store_source):
        if context is None:
            if settings.active_langfuse is None:
                raise ValueError(
                    "Langfuse requires LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY "
                    "and LANGFUSE_BASE_URL, or an enabled caller-supplied context."
                )
            from utils import langfuse as langfuse_utils

            session_id = (
                f"{dataset_config.name.replace('/', '_')}_"
                f"{datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')}"
            )
            context = langfuse_utils.get_langfuse_context(
                session_id=session_id,
                eval_type=dataset_config.component,
                metadata={"dataset": dataset_config.dataset},
                tags=[dataset_config.dataset],
                settings=settings,
            )
            owns_context = True
        context = _require_langfuse_context(context)

    return EvalBackends(
        dataset=DATASET_FACTORIES[dataset_source](context),
        runner=RUNNER_FACTORIES[settings.eval.engine](),
        artefacts=ARTEFACT_FACTORIES[artefact_store_source](context, owns_context),
    )
