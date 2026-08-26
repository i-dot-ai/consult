import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
import utils_gateway  # noqa: E402
from settings import get_settings  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_eval_settings_cache():
    """Clear the `get_settings()` singleton around every test.

    Without this, the first test to call `get_settings()` would poison the
    cache for every subsequent test expecting a different env var value,
    since `lru_cache` never re-reads after the first call — silently
    breaking the existing `monkeypatch.setenv(...)` usage elsewhere in this
    test suite.
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_gateway_model(
    name: str,
    family: str | None = "gpt",
    health: str = "healthy",
    supports_reasoning: bool = False,
) -> utils_gateway.GatewayModel:
    """Shared GatewayModel test fixture builder for test_utils_gateway.py / test_benchmark.py."""
    return utils_gateway.GatewayModel(
        name=name, family=family, health=health, supports_reasoning=supports_reasoning
    )
