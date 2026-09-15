import pytest
import settings
from settings import DEFAULTS, get_settings

# Test values, named once and reused both when setting env vars and when
# asserting on the resulting settings — so no value is retyped by hand in a
# second place where it could drift out of sync with the first.
LANGFUSE_SECRET_KEY = "sk-test"  # pragma: allowlist secret
LANGFUSE_PUBLIC_KEY = "pk-test"
LANGFUSE_BASE_URL = "https://langfuse.example.invalid"
LANGFUSE_PROJECT_ID = "proj-123"

GATEWAY_URL = "https://gateway.example.invalid"
GATEWAY_API_KEY = "test-key"  # pragma: allowlist secret

AUTO_EVAL_MODEL = "gpt-4.1-test"
ENVIRONMENT = "production"
GITHUB_SHA = "abcdef1234567890"  # pragma: allowlist secret
GITHUB_SHA_SHORT = GITHUB_SHA[:7]

# "pydantic_evals" is the only value EvalRunnerSource currently allows — used
# here as an explicit env var override to prove the field is actually read
# from the environment, not just defaulted.
EXPLICIT_ENGINE = DEFAULTS.engine


def _set_langfuse_creds(
    monkeypatch,
    secret=LANGFUSE_SECRET_KEY,
    public=LANGFUSE_PUBLIC_KEY,
    base=LANGFUSE_BASE_URL,
    project=None,
):
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", secret)
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", public)
    monkeypatch.setenv("LANGFUSE_BASE_URL", base)
    if project is not None:
        monkeypatch.setenv("LANGFUSE_PROJECT_ID", project)


def _set_sources(monkeypatch, dataset_source=None, artefact_store=None):
    """Set or clear THEMEFINDER_EVAL_DATASET_SOURCE/_ARTEFACT_STORE together —
    they're always read and reasoned about as a pair."""
    for var, value in (
        ("THEMEFINDER_EVAL_DATASET_SOURCE", dataset_source),
        ("THEMEFINDER_EVAL_ARTEFACT_STORE", artefact_store),
    ):
        if value is None:
            monkeypatch.delenv(var, raising=False)
        else:
            monkeypatch.setenv(var, value)


def _set_gateway_creds(monkeypatch, url=GATEWAY_URL, api_key=GATEWAY_API_KEY):
    monkeypatch.setenv("LLM_GATEWAY_URL", url)
    monkeypatch.setenv("CONSULT_EVAL_LITELLM_API_KEY", api_key)


class TestGetSettingsFieldMapping:
    def test_gateway_fields(self, monkeypatch):
        _set_gateway_creds(monkeypatch)

        s = get_settings()

        assert s.gateway.url == GATEWAY_URL
        assert s.gateway.api_key == GATEWAY_API_KEY

    def test_langfuse_fields(self, monkeypatch):
        _set_langfuse_creds(monkeypatch, project=LANGFUSE_PROJECT_ID)
        _set_sources(monkeypatch, dataset_source="langfuse")

        s = get_settings()

        assert s.langfuse is not None
        assert s.langfuse.secret_key == LANGFUSE_SECRET_KEY
        assert s.langfuse.public_key == LANGFUSE_PUBLIC_KEY
        assert s.langfuse.base_url == LANGFUSE_BASE_URL
        assert s.langfuse.project_id == LANGFUSE_PROJECT_ID

    def test_eval_run_fields(self, monkeypatch):
        monkeypatch.setenv("THEMEFINDER_EVAL_ENGINE", EXPLICIT_ENGINE)
        _set_sources(monkeypatch, dataset_source="langfuse", artefact_store="langfuse")

        s = get_settings()

        assert s.eval.engine == EXPLICIT_ENGINE
        assert s.eval.dataset_source == "langfuse"
        assert s.eval.artefact_store == "langfuse"

    def test_flat_fields(self, monkeypatch):
        monkeypatch.setenv("AUTO_EVAL_MODEL", AUTO_EVAL_MODEL)
        monkeypatch.setenv("ENVIRONMENT", ENVIRONMENT)
        monkeypatch.setenv("GITHUB_SHA", GITHUB_SHA)

        s = get_settings()

        assert s.auto_eval_model == AUTO_EVAL_MODEL
        assert s.environment == ENVIRONMENT
        assert s.git_sha == GITHUB_SHA_SHORT

    def test_defaults_when_unset(self, monkeypatch):
        # get_settings() calls dotenv.load_dotenv() internally, which would
        # otherwise refill any var deleted below straight back out of the
        # real .env file on disk (dotenv only fills in *missing* vars, so a
        # deleted-then-reloaded var looks "unset" to monkeypatch but isn't).
        # Neutralise it so this test exercises the code's actual defaults.
        monkeypatch.setattr(settings.dotenv, "load_dotenv", lambda *a, **k: None)
        for var in (
            "ENVIRONMENT",
            "GITHUB_SHA",
            "THEMEFINDER_EVAL_ENGINE",
            "AUTO_EVAL_MODEL",
        ):
            monkeypatch.delenv(var, raising=False)
        _set_sources(monkeypatch)

        s = get_settings()

        assert s.environment == DEFAULTS.environment
        assert s.git_sha == DEFAULTS.git_sha
        assert s.eval.engine == DEFAULTS.engine
        assert s.eval.dataset_source is None
        assert s.eval.artefact_store is None
        assert s.auto_eval_model is None
        assert s.langfuse is None
        assert s.active_langfuse is None


class TestLangfusePopulation:
    """`settings.langfuse`/`.active_langfuse` follow one rule: populated only
    when a selector explicitly asks for "langfuse"; None otherwise — whether
    both selectors are unset, both explicitly "local", or credentials happen
    to be present without either selector naming Langfuse (the scenario this
    design exists for: don't let stray LANGFUSE_* — a shared `.env`, a
    leftover shell export — pull a run into using Langfuse it never asked for)."""

    @pytest.mark.parametrize(
        "dataset_source,artefact_store",
        [("langfuse", "local"), ("local", "langfuse"), ("langfuse", "langfuse")],
    )
    def test_populated_and_active_when_either_selector_is_langfuse(
        self, monkeypatch, dataset_source, artefact_store
    ):
        _set_langfuse_creds(monkeypatch)
        _set_sources(
            monkeypatch, dataset_source=dataset_source, artefact_store=artefact_store
        )

        s = get_settings()

        assert s.langfuse is not None
        assert s.langfuse.configured is True
        assert s.active_langfuse is s.langfuse

    @pytest.mark.parametrize(
        "dataset_source,artefact_store",
        [(None, None), ("local", None), (None, "local"), ("local", "local")],
    )
    def test_not_populated_without_an_explicit_langfuse_selector(
        self, monkeypatch, dataset_source, artefact_store
    ):
        _set_langfuse_creds(monkeypatch)  # full creds present, but not selected
        _set_sources(
            monkeypatch, dataset_source=dataset_source, artefact_store=artefact_store
        )

        s = get_settings()

        assert s.langfuse is None
        assert s.active_langfuse is None

    def test_populated_but_not_active_when_credentials_incomplete(self, monkeypatch):
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", LANGFUSE_SECRET_KEY)
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_BASE_URL", raising=False)
        _set_sources(monkeypatch, dataset_source="langfuse")

        s = get_settings()

        assert s.langfuse is not None
        assert s.langfuse.configured is False
        assert s.active_langfuse is None


class TestGetSettingsCaching:
    def test_repeated_calls_return_same_object(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", ENVIRONMENT)

        first = get_settings()
        second = get_settings()

        assert first is second
        assert second.environment == ENVIRONMENT

    def test_cache_clear_picks_up_new_env_value(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "before")
        assert get_settings().environment == "before"

        get_settings.cache_clear()
        monkeypatch.setenv("ENVIRONMENT", ENVIRONMENT)

        assert get_settings().environment == ENVIRONMENT


class TestEvalSettingsSingleton:
    def test_matches_get_settings_for_the_real_environment(self):
        """`settings.eval_settings` was computed once, via get_settings(), at
        import time. Every other test in this file monkeypatches env vars to
        exercise get_settings() directly — this is the one test that instead
        confirms the singleton itself is just get_settings() under whatever
        real environment (.env file, actual process env) this test run has,
        with nothing monkeypatched."""
        assert settings.eval_settings == get_settings()
