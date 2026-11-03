"""Centralised env-var reading for `themefinder/evals/`.

Deliberately not named `config.py`, to avoid confusion with `evals/config.py`
(which wires adapters together; this module just reads env vars).

Runtime modules read the matching field from `eval_settings`, the process-wide
settings snapshot created below. `get_settings()` constructs that snapshot and
is retained for focused settings tests; application code must not call it as a
hidden dependency.

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

# "local" runs cases sequentially in-process, with no native eval engine.
EvalRunnerSource = Literal["pydantic_evals", "local"]
EvalBackendSource = Literal["langfuse", "local"]
LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]


@dataclass(frozen=True)
class _Defaults:
    """The fallbacks get_settings() uses when their env var is unset."""

    environment: str = "development"
    git_sha: str = "local"
    engine: EvalRunnerSource = "pydantic_evals"
    log_level: LogLevel = "INFO"


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
    langfuse: LangfuseSettings
    eval: EvalRunSettings
    log_level: LogLevel
    # Separate from auto_eval_model so judge calls never reuse the model under test
    judge_model: str | None = None

    @property
    def active_langfuse(self) -> LangfuseSettings | None:
        """The Langfuse settings when the credentials are complete; else None.

        Tracing follows this alone, so a run traces whenever a Langfuse
        connection is available. The dataset and artefact selectors only
        decide where cases are read from and results written to.
        """
        if self.langfuse.configured:
            return self.langfuse
        return None


@lru_cache(maxsize=1)
def get_settings() -> EvalSettings:
    eval_run = EvalRunSettings(
        engine=os.getenv("THEMEFINDER_EVAL_ENGINE", DEFAULTS.engine),
        dataset_source=os.getenv("THEMEFINDER_EVAL_DATASET_SOURCE"),
        artefact_store=os.getenv("THEMEFINDER_EVAL_ARTEFACT_STORE"),
    )

    return EvalSettings(
        auto_eval_model=os.getenv("AUTO_EVAL_MODEL"),
        judge_model=os.getenv("AUTO_EVAL_JUDGE_MODEL"),
        environment=os.getenv("ENVIRONMENT", DEFAULTS.environment),
        git_sha=os.getenv("GITHUB_SHA", DEFAULTS.git_sha)[:7],
        gateway=GatewaySettings(
            url=os.getenv("LLM_GATEWAY_URL"),
            api_key=os.getenv("CONSULT_EVAL_LITELLM_API_KEY"),
        ),
        langfuse=LangfuseSettings(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            base_url=os.getenv("LANGFUSE_BASE_URL"),
            project_id=os.getenv("LANGFUSE_PROJECT_ID"),
        ),
        eval=eval_run,
        log_level=os.getenv("THEMEFINDER_EVAL_LOG_LEVEL", DEFAULTS.log_level).upper(),
    )


eval_settings = get_settings()
