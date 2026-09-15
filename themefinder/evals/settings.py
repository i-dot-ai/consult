"""Centralised env-var reading for `themefinder/evals/`.

Deliberately not named `config.py`, to avoid confusion with `evals/config.py`
(which wires adapters together; this module just reads env vars).

Every module that used to call `os.getenv(...)` / `os.environ.get(...)`
directly for one of these settings should instead call `get_settings()` and
read the matching field. `get_settings()` is a process-wide cached singleton:
env vars are read once, `.env` is loaded once, regardless of how many modules
ask.

The settings dataclasses below use `pydantic.dataclasses.dataclass`, not the
stdlib one — plain stdlib dataclasses don't validate their fields against
their type hints at construction time, so a `Literal["langfuse", "local"]`
field would silently accept an env var set to anything at all. Pydantic
validates on construction (`pydantic>=2.0.0` is already a core dependency),
so a typo like `THEMEFINDER_EVAL_DATASET_SOURCE=langfuze` raises here, with
the actual bad value in the error, instead of surfacing later as a confusing
mismatch downstream.
"""

import os
from functools import lru_cache
from typing import Literal

import dotenv
from pydantic.dataclasses import dataclass

# Loaded once here at import time rather than inside get_settings(): that
# function is an lru_cache singleton anyway and allows tests to change env variables.
dotenv.load_dotenv()

# Just a single valid value for THEMEFINDER_EVAL_ENGINE at the moment, but allows for future expansion.
EvalRunnerSource = Literal["pydantic_evals"]
EvalBackendSource = Literal["langfuse", "local"]


@dataclass(frozen=True)
class _Defaults:
    """The fallbacks get_settings() uses when their env var is unset."""

    environment: str = "development"
    git_sha: str = "local"
    engine: EvalRunnerSource = "pydantic_evals"


DEFAULTS = _Defaults()


@dataclass(frozen=True)
class LangfuseSettings:
    secret_key: str | None
    public_key: str | None
    base_url: str | None
    project_id: str | None

    @property
    def configured(self) -> bool:
        return bool(self.secret_key and self.public_key and self.base_url)


@dataclass(frozen=True)
class GatewaySettings:
    # Optional here even though callers need both set — os.getenv() returns
    # None when unset, and get_settings() must succeed for every caller, not
    # just ones that touch the gateway. gateway.gateway_credentials()
    # is where "both required" is actually enforced, with a caller-facing
    # RuntimeError naming the two env vars to set.
    url: str | None
    api_key: str | None


@dataclass(frozen=True)
class EvalRunSettings:
    engine: EvalRunnerSource
    dataset_source: EvalBackendSource | None
    artefact_store: EvalBackendSource | None


@dataclass(frozen=True)
class EvalSettings:
    auto_eval_model: str | None
    environment: str
    git_sha: str
    gateway: GatewaySettings
    # None when this run has explicitly ruled Langfuse out (both
    # THEMEFINDER_EVAL_DATASET_SOURCE and THEMEFINDER_EVAL_ARTEFACT_STORE set
    # to something other than "langfuse") — distinguishes "deliberately not
    # using Langfuse" from "configured with incomplete/absent credentials".
    langfuse: LangfuseSettings | None
    eval: EvalRunSettings

    @property
    def active_langfuse(self) -> LangfuseSettings | None:
        """The Langfuse settings, if this run has them and they're complete; else None.

        Checks langfuse settings are available and correctly configured
        """
        if self.langfuse is not None and self.langfuse.configured:
            return self.langfuse
        return None


def _wants_langfuse(
    dataset_source: EvalBackendSource | None, artefact_store: EvalBackendSource | None
) -> bool:
    """Whether this run might use Langfuse, from the two selectors alone.

    Populate `EvalSettings.langfuse` whenever either selector explicitly asks
    for "langfuse".
    """
    return dataset_source == "langfuse" or artefact_store == "langfuse"


@lru_cache(maxsize=1)
def get_settings() -> EvalSettings:
    eval_run = EvalRunSettings(
        engine=os.getenv("THEMEFINDER_EVAL_ENGINE", DEFAULTS.engine),
        dataset_source=os.getenv("THEMEFINDER_EVAL_DATASET_SOURCE"),
        artefact_store=os.getenv("THEMEFINDER_EVAL_ARTEFACT_STORE"),
    )

    langfuse = None
    if _wants_langfuse(eval_run.dataset_source, eval_run.artefact_store):
        langfuse = LangfuseSettings(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            base_url=os.getenv("LANGFUSE_BASE_URL"),
            project_id=os.getenv("LANGFUSE_PROJECT_ID"),
        )

    return EvalSettings(
        auto_eval_model=os.getenv("AUTO_EVAL_MODEL"),
        environment=os.getenv("ENVIRONMENT", DEFAULTS.environment),
        git_sha=os.getenv("GITHUB_SHA", DEFAULTS.git_sha)[:7],
        gateway=GatewaySettings(
            url=os.getenv("LLM_GATEWAY_URL"),
            api_key=os.getenv("CONSULT_EVAL_LITELLM_API_KEY"),
        ),
        langfuse=langfuse,
        eval=eval_run,
    )


eval_settings = get_settings()
