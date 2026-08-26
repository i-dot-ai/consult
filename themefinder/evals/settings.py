"""Centralised env-var reading for `themefinder/evals/`.

Deliberately not named `config.py`, to avoid confusion with `evals/config.py`
(which wires adapters together; this module just reads env vars).

Every module that used to call `os.getenv(...)` / `os.environ.get(...)`
directly for one of these settings should instead call `get_settings()` and
read the matching field. `get_settings()` is a process-wide cached singleton:
env vars are read once, `.env` is loaded once, regardless of how many modules
ask.
"""

import os
from dataclasses import dataclass
from functools import lru_cache

import dotenv


@dataclass(frozen=True)
class EvalSettings:
    auto_eval_model: str | None
    llm_gateway_url: str | None
    llm_gateway_api_key: str | None
    langfuse_secret_key: str | None
    langfuse_public_key: str | None
    langfuse_base_url: str | None
    langfuse_project_id: str | None
    environment: str
    git_sha: str
    eval_engine: str
    # "langfuse" | "local" | None (None = follow resolve_backends' own
    # default: "langfuse" if credentials are set, else "local")
    eval_dataset_source: str | None
    # Same values, same default rule, resolved independently.
    eval_artefact_store: str | None


@lru_cache(maxsize=1)
def get_settings() -> EvalSettings:
    dotenv.load_dotenv()
    return EvalSettings(
        auto_eval_model=os.getenv("AUTO_EVAL_MODEL"),
        llm_gateway_url=os.getenv("LLM_GATEWAY_URL"),
        llm_gateway_api_key=os.getenv("CONSULT_EVAL_LITELLM_API_KEY"),
        langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        langfuse_base_url=os.getenv("LANGFUSE_BASE_URL"),
        langfuse_project_id=os.getenv("LANGFUSE_PROJECT_ID"),
        environment=os.getenv("ENVIRONMENT", "development"),
        git_sha=os.getenv("GITHUB_SHA", "local")[:7],
        eval_engine=os.getenv("THEMEFINDER_EVAL_ENGINE", "pydantic_evals"),
        eval_dataset_source=os.getenv("THEMEFINDER_EVAL_DATASET_SOURCE"),
        eval_artefact_store=os.getenv("THEMEFINDER_EVAL_ARTEFACT_STORE"),
    )
