"""Discover chat-capable models available on the LLM gateway."""

import asyncio
from dataclasses import dataclass

import httpx
from settings import eval_settings

# TODO: hardcoded substring matching for a small, manually maintained subset
# of model families. New model names (e.g. a future o-series release) won't
# be recognised until added here by hand. Replace with a proper family field
# once the gateway exposes that as metadata, rather than us inferring it.
_FAMILY_SUBSTRINGS = ("claude", "gemini", "locai")
_GPT_MARKERS = ("gpt", "o4-", "o1-", "o3-")

# Every family derive_family() can return (besides None).
KNOWN_FAMILIES = (*_FAMILY_SUBSTRINGS, "gpt")


@dataclass(frozen=True)
class GatewayModel:
    name: str
    family: str | None
    health: str  # "healthy" | "unhealthy" | "unknown"
    supports_reasoning: bool = False


# Prefer the same paginated v2 endpoint the gateway frontend uses, then fall
# back through the alternate routes still used elsewhere.
MODEL_INFO_PATHS = (
    "/v2/model/info",
    "/model/info",
)

MAX_MODEL_INFO_PAGES = 100


def derive_family(name: str) -> str | None:
    """Bucket a model name into a known vendor family (claude/gemini/locai/gpt) by substring match."""
    lowered = name.lower()
    for family in _FAMILY_SUBSTRINGS:
        if family in lowered:
            return family
    if any(marker in lowered for marker in _GPT_MARKERS):
        return "gpt"
    return None


def filter_by_family(
    models: list[GatewayModel], families: list[str]
) -> list[GatewayModel]:
    """Return models whose family matches any of the given families."""
    family_set = set(families)
    return [m for m in models if m.family in family_set]


def split_unhealthy(
    models: list[GatewayModel],
) -> tuple[list[GatewayModel], list[GatewayModel]]:
    """Split models into (kept, unhealthy) by current gateway health snapshot.

    Models with no health data ("unknown") are kept — absence of
    evidence isn't evidence of a problem.
    """
    kept = []
    unhealthy = []
    for m in models:
        if m.health == "unhealthy":
            unhealthy.append(m)
        else:
            kept.append(m)
    return kept, unhealthy


def select_by_name(
    models: list[GatewayModel], names: list[str]
) -> tuple[list[GatewayModel], list[str]]:
    """Split requested names into found models and names not on the gateway."""
    by_name = {m.name: m for m in models}
    found = []
    missing = []
    for name in names:
        if name in by_name:
            found.append(by_name[name])
        else:
            missing.append(name)
    return found, missing


def filter_chat_models(model_group_items: list[dict]) -> list[dict]:
    """Return model entries that support chat completions."""
    return [item for item in model_group_items if _item_mode(item) == "chat"]


def _item_model_info(item: dict) -> dict:
    model_info = item.get("model_info")
    return model_info if isinstance(model_info, dict) else {}


def _item_name(item: dict) -> str | None:
    return item.get("model_name") or item.get("model_group") or item.get("id")


def _item_mode(item: dict) -> str | None:
    if "mode" in item:
        return item.get("mode")
    return _item_model_info(item).get("mode")


def _item_model_id(item: dict) -> str | None:
    model_id = _item_model_info(item).get("id") or item.get("model_id")
    return model_id if isinstance(model_id, str) else None


def _item_supports_reasoning(item: dict) -> bool:
    item_supported_reasoning_efforts = item.get("supported_reasoning_efforts")
    if isinstance(item_supported_reasoning_efforts, list):
        return bool(item_supported_reasoning_efforts)

    item_supports_reasoning = item.get("supports_reasoning")
    if isinstance(item_supports_reasoning, bool):
        return item_supports_reasoning

    model_info = _item_model_info(item)
    model_supported_reasoning_efforts = model_info.get("supported_reasoning_efforts")
    if isinstance(model_supported_reasoning_efforts, list):
        return bool(model_supported_reasoning_efforts)

    model_supports_reasoning = model_info.get("supports_reasoning")
    if isinstance(model_supports_reasoning, bool):
        return model_supports_reasoning

    return False


def _health_snapshot_records(health_body: dict) -> list[tuple[str, dict]]:
    if not isinstance(health_body, dict):
        raise TypeError("Health response must be an object")

    healthy = health_body.get("healthy_endpoints")
    unhealthy = health_body.get("unhealthy_endpoints")
    if not isinstance(healthy, list) or not isinstance(unhealthy, list):
        raise TypeError(
            "Health response missing healthy_endpoints/unhealthy_endpoints lists"
        )

    return [("healthy", record) for record in healthy if isinstance(record, dict)] + [
        ("unhealthy", record) for record in unhealthy if isinstance(record, dict)
    ]


def health_by_model_id(health_body: dict) -> dict[str, str]:
    """Return the current gateway health status for each health-check model id."""
    by_model_id: dict[str, str] = {}
    for status, record in _health_snapshot_records(health_body):
        model_id = record.get("model_id") or record.get("id")
        if isinstance(model_id, str):
            by_model_id[model_id] = status
    return by_model_id


def _resolve_item_health(item: dict, status_by_model_id: dict[str, str]) -> str:
    model_id = _item_model_id(item)
    if model_id is not None and model_id in status_by_model_id:
        return status_by_model_id[model_id]
    return "unknown"


def _merge_health(existing: str, new: str) -> str:
    if "unhealthy" in {existing, new}:
        return "unhealthy"
    if "healthy" in {existing, new}:
        return "healthy"
    return "unknown"


def _dedupe_models_by_name(models: list[GatewayModel]) -> list[GatewayModel]:
    deduped: dict[str, GatewayModel] = {}
    for model in models:
        existing = deduped.get(model.name)
        if existing is None:
            deduped[model.name] = model
            continue

        deduped[model.name] = GatewayModel(
            name=model.name,
            family=existing.family or model.family,
            health=_merge_health(existing.health, model.health),
            supports_reasoning=existing.supports_reasoning or model.supports_reasoning,
        )

    return list(deduped.values())


def gateway_credentials() -> tuple[str, str]:
    """Read and validate the two required gateway env vars."""
    base_url = eval_settings.gateway.url
    api_key = eval_settings.gateway.api_key
    if not base_url or not api_key:
        raise RuntimeError(
            "LLM_GATEWAY_URL and CONSULT_EVAL_LITELLM_API_KEY must be set"
        )
    return base_url, api_key


def _gateway_client() -> httpx.AsyncClient:
    base_url, api_key = gateway_credentials()
    return httpx.AsyncClient(
        base_url=base_url.rstrip("/"),
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )


def _parse_model_info_page(body: dict) -> tuple[list[dict], int | None, int | None]:
    data = body.get("data")
    if not isinstance(data, list):
        raise TypeError("Model info response missing data list")
    current_page = body.get("current_page")
    total_pages = body.get("total_pages")
    return data, current_page, total_pages


async def _fetch_model_info_pages(client: httpx.AsyncClient, path: str) -> list[dict]:
    page = 1
    items: list[dict] = []
    while True:
        if page > MAX_MODEL_INFO_PAGES:
            raise RuntimeError(
                f"Aborting model-info fetch after {MAX_MODEL_INFO_PAGES} pages from {path}"
            )

        response = await client.get(path, params={"page": str(page)})
        response.raise_for_status()
        page_items, current_page, total_pages = _parse_model_info_page(response.json())
        items.extend(page_items)

        if current_page is None or total_pages is None or current_page >= total_pages:
            return items

        page += 1


async def fetch_model_info(client: httpx.AsyncClient) -> list[dict]:
    fallback_errors: list[httpx.HTTPStatusError] = []
    for index, path in enumerate(MODEL_INFO_PATHS):
        try:
            return await _fetch_model_info_pages(client, path)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403):
                fallback_errors.append(exc)
                continue

            if exc.response.status_code == 404 and index < len(MODEL_INFO_PATHS) - 1:
                fallback_errors.append(exc)
                continue

            if exc.response.status_code == 404:
                tried = ", ".join(MODEL_INFO_PATHS)
                raise RuntimeError(
                    "The gateway did not expose a usable rich model-info route. "
                    f"Tried: {tried}. Last failure: {exc.request.url.path} "
                    f"(HTTP {exc.response.status_code})."
                ) from exc

            raise

    if fallback_errors:
        last_error = fallback_errors[-1]
        tried = ", ".join(MODEL_INFO_PATHS)
        raise RuntimeError(
            "CONSULT_EVAL_LITELLM_API_KEY lacks access to a rich model-info route. "
            f"Tried: {tried}. Last failure: {last_error.request.url.path} "
            f"(HTTP {last_error.response.status_code}). Please ensure that the "
            "allowed routes for this key include at least one model-info route "
            "and /health."
        ) from last_error

    raise RuntimeError("No model-info routes returned usable data")


async def fetch_health(client: httpx.AsyncClient) -> dict:
    response = await client.get("/health")
    response.raise_for_status()
    body = response.json()
    try:
        _health_snapshot_records(body)
    except TypeError as exc:
        raise RuntimeError(
            "/health returned an unexpected response shape "
            "(missing healthy_endpoints/unhealthy_endpoints lists)"
        ) from exc
    return body


async def discover_chat_models() -> list[GatewayModel]:
    """Fetch every chat-capable gateway model with its family and health resolved."""
    async with _gateway_client() as client:
        try:
            model_info_items, health_body = await asyncio.gather(
                fetch_model_info(client),
                fetch_health(client),
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403):
                raise RuntimeError(
                    f"CONSULT_EVAL_LITELLM_API_KEY lacks access to {exc.request.url.path} "
                    f"(HTTP {exc.response.status_code}). Please ensure that the allowed "
                    "paths for this key are correctly set via the LLM gateway UI."
                ) from exc
            raise

    # A key whose model grant is a wildcard (e.g. "all-team-models") can get
    # this route back unexpanded - a single "*" row instead of individual
    # models - rather than a real list to discover from.
    if any(_item_name(item) == "*" for item in model_info_items):
        raise RuntimeError(
            "The gateway returned an unexpanded '*' entry instead of individual "
            "model names - this requires checking the settings in the model gateway."
        )

    chat_models = filter_chat_models(model_info_items)
    status_by_model_id = health_by_model_id(health_body)

    return _dedupe_models_by_name(
        [
            GatewayModel(
                name=name,
                family=derive_family(name),
                health=_resolve_item_health(item, status_by_model_id),
                supports_reasoning=_item_supports_reasoning(item),
            )
            for item in chat_models
            if (name := _item_name(item)) is not None
        ]
    )
