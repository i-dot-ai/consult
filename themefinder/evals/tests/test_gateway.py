from typing import ClassVar

import httpx
import pytest
from conftest import make_gateway_model, set_gateway_credentials
from utils import gateway


def _health_row(model_id: str, *, model: str | None = None, error: str | None = None):
    row = {"model_id": model_id}
    if model is not None:
        row["model"] = model
    if error is not None:
        row["error"] = error
    return row


def _health_snapshot(
    *, healthy: list[dict] | None = None, unhealthy: list[dict] | None = None
) -> dict:
    return {
        "healthy_endpoints": healthy or [],
        "unhealthy_endpoints": unhealthy or [],
    }


def _model_info(
    model_name: str,
    *,
    mode: str = "chat",
    model_info_id: str | None = None,
    supports_reasoning: bool = False,
    supported_reasoning_efforts: list[str] | None = None,
) -> dict:
    model_info = {
        "id": model_info_id or f"{model_name}-id",
        "mode": mode,
        "supports_reasoning": supports_reasoning,
    }
    if supported_reasoning_efforts is not None:
        model_info["supported_reasoning_efforts"] = supported_reasoning_efforts
    return {
        "model_name": model_name,
        "model_info": model_info,
    }


class TestFilterChatModels:
    def test_keeps_only_chat_mode(self):
        items = [
            _model_info("gpt-4o"),
            _model_info("dall-e-3", mode="image_generation"),
            _model_info("text-embedding-3", mode="embedding"),
        ]
        assert gateway.filter_chat_models(items) == [items[0]]


class TestHealthMappings:
    def test_health_by_model_id_maps_snapshot(self):
        health_body = _health_snapshot(
            healthy=[_health_row("gpt-4o-id")],
            unhealthy=[_health_row("claude-haiku-id", error="boom")],
        )

        assert gateway.health_by_model_id(health_body) == {
            "gpt-4o-id": "healthy",
            "claude-haiku-id": "unhealthy",
        }

    def test_invalid_snapshot_shape_raises(self):
        with pytest.raises(TypeError, match="healthy_endpoints"):
            gateway.health_by_model_id({})


class TestDeriveFamily:
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("gpt-4.1-sweden", "gpt"),
            ("o3-mini", "gpt"),
            ("claude-haiku-4.5", "claude"),
            ("gemini-2.5-flash", "gemini"),
            ("locailabs/locai-l1-large-2011", "locai"),
            ("mistral-large", None),
        ],
    )
    def test_family_bucket(self, name, expected):
        assert gateway.derive_family(name) == expected


class TestFilterByFamily:
    MODELS: ClassVar[list[gateway.GatewayModel]] = [
        make_gateway_model(name="gpt-4o", family="gpt"),
        make_gateway_model(name="claude-haiku", family="claude"),
        make_gateway_model(name="gemini-flash", family="gemini"),
        make_gateway_model(name="bedrock-qwen3", family=None),
    ]

    def test_single_family(self):
        result = gateway.filter_by_family(self.MODELS, ["claude"])
        assert [m.name for m in result] == ["claude-haiku"]

    def test_multiple_families(self):
        result = gateway.filter_by_family(self.MODELS, ["gemini", "claude"])
        assert {m.name for m in result} == {"gemini-flash", "claude-haiku"}

    def test_no_match_returns_empty(self):
        assert gateway.filter_by_family(self.MODELS, ["locai"]) == []


class TestSelectByName:
    MODELS: ClassVar[list[gateway.GatewayModel]] = [
        make_gateway_model(name="gpt-4o", family="gpt"),
        make_gateway_model(name="claude-haiku", family="claude", health="unhealthy"),
    ]

    def test_all_found(self):
        found, missing = gateway.select_by_name(self.MODELS, ["gpt-4o", "claude-haiku"])
        assert {m.name for m in found} == {"gpt-4o", "claude-haiku"}
        assert missing == []

    def test_some_missing(self):
        found, missing = gateway.select_by_name(self.MODELS, ["gpt-4o", "typo-model"])
        assert [m.name for m in found] == ["gpt-4o"]
        assert missing == ["typo-model"]

    def test_found_model_keeps_its_health_status(self):
        found, _ = gateway.select_by_name(self.MODELS, ["claude-haiku"])
        assert found[0].health == "unhealthy"


class TestSplitUnhealthy:
    MODELS: ClassVar[list[gateway.GatewayModel]] = [
        make_gateway_model(name="gpt-4o", family="gpt"),
        make_gateway_model(name="claude-haiku", family="claude", health="unhealthy"),
        make_gateway_model(name="mystery-model", family=None, health="unknown"),
    ]

    def test_keeps_healthy_and_unknown_splits_out_unhealthy(self):
        kept, unhealthy = gateway.split_unhealthy(self.MODELS)
        assert {m.name for m in kept} == {"gpt-4o", "mystery-model"}
        assert [m.name for m in unhealthy] == ["claude-haiku"]


class TestFetchModelInfo:
    async def test_prefers_v2_model_info_route_first(self, monkeypatch):
        class FakeClient:
            def __init__(self):
                self.calls = []

            async def get(self, path, params=None):
                self.calls.append((path, params))

                class FakeResponse:
                    def raise_for_status(self):
                        return None

                    def json(self):
                        return {
                            "data": [_model_info("gpt-4o", supports_reasoning=True)],
                            "current_page": 1,
                            "total_pages": 1,
                        }

                return FakeResponse()

        client = FakeClient()
        result = await gateway.fetch_model_info(client)

        assert result == [_model_info("gpt-4o", supports_reasoning=True)]
        assert client.calls == [("/v2/model/info", {"page": "1"})]

    async def test_falls_back_to_next_rich_route_on_permission_error(self, monkeypatch):
        request = httpx.Request("GET", "https://gateway.example.invalid/v2/model/info")
        response = httpx.Response(403, request=request)

        class FakeClient:
            def __init__(self):
                self.calls = []

            async def get(self, path, params=None):
                self.calls.append((path, params))
                if path == "/v2/model/info":
                    raise httpx.HTTPStatusError(
                        "403 Forbidden", request=request, response=response
                    )

                class FakeResponse:
                    def raise_for_status(self):
                        return None

                    def json(self):
                        return {
                            "data": [_model_info("gpt-4o")],
                            "current_page": 1,
                            "total_pages": 1,
                        }

                return FakeResponse()

        client = FakeClient()
        result = await gateway.fetch_model_info(client)

        assert result == [_model_info("gpt-4o")]
        assert [call[0] for call in client.calls] == ["/v2/model/info", "/model/info"]

    async def test_final_404_raises_clear_runtime_error(self, monkeypatch):
        class FakeClient:
            def __init__(self):
                self.calls = []

            async def get(self, path, params=None):
                self.calls.append((path, params))
                request = httpx.Request("GET", f"https://gateway.example.invalid{path}")
                response = httpx.Response(404, request=request)
                raise httpx.HTTPStatusError(
                    "404 Not Found", request=request, response=response
                )

        client = FakeClient()

        with pytest.raises(RuntimeError, match="usable rich model-info route"):
            await gateway.fetch_model_info(client)

        assert [call[0] for call in client.calls] == ["/v2/model/info", "/model/info"]


class TestFetchHealth:
    async def test_reads_health_snapshot_route(self):
        health_body = _health_snapshot(healthy=[_health_row("gpt-4o-id")])

        class FakeClient:
            def __init__(self):
                self.calls = []

            async def get(self, path):
                self.calls.append(path)

                class FakeResponse:
                    def raise_for_status(self):
                        return None

                    def json(self):
                        return health_body

                return FakeResponse()

        client = FakeClient()
        result = await gateway.fetch_health(client)

        assert result == health_body
        assert client.calls == ["/health"]

    async def test_invalid_snapshot_shape_raises_clear_runtime_error(self):
        class FakeClient:
            async def get(self, path):
                class FakeResponse:
                    def raise_for_status(self):
                        return None

                    def json(self):
                        return {}

                return FakeResponse()

        client = FakeClient()

        with pytest.raises(RuntimeError, match="/health returned an unexpected"):
            await gateway.fetch_health(client)


class TestDiscoverChatModels:
    async def test_combines_and_resolves_unfiltered(self, monkeypatch):
        model_group_items = [
            _model_info("gpt-4o"),
            _model_info("claude-haiku"),
            _model_info("gemini-flash", supports_reasoning=True),
            _model_info("mystery-model"),
            _model_info("text-embedding-3", mode="embedding"),
        ]
        health_body = _health_snapshot(
            healthy=[_health_row("gpt-4o-id")],
            unhealthy=[_health_row("claude-haiku-id", error="boom")],
        )

        async def fake_model_info(client):
            return model_group_items

        async def fake_health(client):
            return health_body

        monkeypatch.setattr(gateway, "fetch_model_info", fake_model_info)
        monkeypatch.setattr(gateway, "fetch_health", fake_health)
        set_gateway_credentials(monkeypatch)

        result = await gateway.discover_chat_models()

        by_name = {m.name: m for m in result}
        # unfiltered: non-chat excluded, but unhealthy/unknown models all present
        assert set(by_name) == {
            "gpt-4o",
            "claude-haiku",
            "gemini-flash",
            "mystery-model",
        }
        assert by_name["gpt-4o"].health == "healthy"
        assert by_name["claude-haiku"].health == "unhealthy"
        assert by_name["gemini-flash"].health == "unknown"  # no health data in snapshot
        assert (
            by_name["mystery-model"].health == "unknown"
        )  # no health data in snapshot
        assert by_name["gpt-4o"].family == "gpt"
        assert by_name["gemini-flash"].family == "gemini"
        assert by_name["mystery-model"].family is None
        assert by_name["gemini-flash"].supports_reasoning is True
        assert by_name["gpt-4o"].supports_reasoning is False

    async def test_dedupes_duplicate_model_names_conservatively(self, monkeypatch):
        model_group_items = [
            _model_info(
                "gpt-5.2-uk+sweden",
                model_info_id="duplicate-a",
                supports_reasoning=False,
            ),
            _model_info(
                "gpt-5.2-uk+sweden",
                model_info_id="duplicate-b",
                supports_reasoning=True,
            ),
        ]
        health_body = _health_snapshot(
            healthy=[_health_row("duplicate-a")],
            unhealthy=[_health_row("duplicate-b", error="boom")],
        )

        async def fake_model_info(client):
            return model_group_items

        async def fake_health(client):
            return health_body

        monkeypatch.setattr(gateway, "fetch_model_info", fake_model_info)
        monkeypatch.setattr(gateway, "fetch_health", fake_health)
        set_gateway_credentials(monkeypatch)

        result = await gateway.discover_chat_models()

        assert len(result) == 1
        assert result[0].name == "gpt-5.2-uk+sweden"
        assert result[0].health == "unhealthy"
        assert result[0].supports_reasoning is True

    async def test_missing_supports_reasoning_defaults_false(self, monkeypatch):
        model_group_items = [{"model_name": "gpt-4o", "model_info": {"mode": "chat"}}]

        async def fake_model_info(client):
            return model_group_items

        async def fake_health(client):
            return _health_snapshot()

        monkeypatch.setattr(gateway, "fetch_model_info", fake_model_info)
        monkeypatch.setattr(gateway, "fetch_health", fake_health)
        set_gateway_credentials(monkeypatch)

        result = await gateway.discover_chat_models()

        assert result[0].supports_reasoning is False

    async def test_supported_reasoning_efforts_marks_model_reasoning_capable(
        self, monkeypatch
    ):
        model_group_items = [
            _model_info(
                "gpt-5-mini",
                supported_reasoning_efforts=["low", "medium", "high"],
            )
        ]

        async def fake_model_info(client):
            return model_group_items

        async def fake_health(client):
            return _health_snapshot()

        monkeypatch.setattr(gateway, "fetch_model_info", fake_model_info)
        monkeypatch.setattr(gateway, "fetch_health", fake_health)
        set_gateway_credentials(monkeypatch)

        result = await gateway.discover_chat_models()

        assert result[0].supports_reasoning is True

    async def test_raises_runtime_error_on_model_info_401(self, monkeypatch):
        request = httpx.Request("GET", "https://gateway.example.invalid/v2/model/info")
        response = httpx.Response(401, request=request)

        async def fake_model_info(client):
            raise httpx.HTTPStatusError(
                "401 Unauthorized", request=request, response=response
            )

        async def fake_health(client):
            return _health_snapshot()

        monkeypatch.setattr(gateway, "fetch_model_info", fake_model_info)
        monkeypatch.setattr(gateway, "fetch_health", fake_health)
        set_gateway_credentials(monkeypatch)

        with pytest.raises(RuntimeError, match="lacks access"):
            await gateway.discover_chat_models()

    async def test_raises_runtime_error_on_health_401(self, monkeypatch):
        request = httpx.Request("GET", "https://gateway.example.invalid/health")
        response = httpx.Response(401, request=request)

        async def fake_model_info(client):
            return [_model_info("gpt-4o")]

        async def fake_health(client):
            raise httpx.HTTPStatusError(
                "401 Unauthorized", request=request, response=response
            )

        monkeypatch.setattr(gateway, "fetch_model_info", fake_model_info)
        monkeypatch.setattr(gateway, "fetch_health", fake_health)
        set_gateway_credentials(monkeypatch)

        with pytest.raises(RuntimeError, match="/health"):
            await gateway.discover_chat_models()

    async def test_non_permission_error_propagates_unchanged(self, monkeypatch):
        request = httpx.Request("GET", "https://gateway.example.invalid/v2/model/info")
        response = httpx.Response(500, request=request)

        async def fake_model_info(client):
            raise httpx.HTTPStatusError(
                "500 Internal Server Error", request=request, response=response
            )

        async def fake_health(client):
            return _health_snapshot()

        monkeypatch.setattr(gateway, "fetch_model_info", fake_model_info)
        monkeypatch.setattr(gateway, "fetch_health", fake_health)
        set_gateway_credentials(monkeypatch)

        # Not a permission error - should propagate as-is, not get converted
        # into the "check your key permissions" RuntimeError.
        with pytest.raises(httpx.HTTPStatusError):
            await gateway.discover_chat_models()

    async def test_raises_runtime_error_on_wildcard_entry(self, monkeypatch):
        model_group_items = [{"model_group": "*", "mode": "chat"}]

        async def fake_model_info(client):
            return model_group_items

        async def fake_health(client):
            return _health_snapshot()

        monkeypatch.setattr(gateway, "fetch_model_info", fake_model_info)
        monkeypatch.setattr(gateway, "fetch_health", fake_health)
        set_gateway_credentials(monkeypatch)

        with pytest.raises(RuntimeError, match="unexpanded"):
            await gateway.discover_chat_models()
