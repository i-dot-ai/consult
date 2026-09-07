from typing import Any

from drf_orjson_renderer.renderers import ORJSONRenderer


def _stringify_keys(obj: Any) -> Any:
    """Recursively convert integer dict keys to strings.

    DRF 3.18.0 changed list serializer errors to use integer-indexed dicts
    (e.g. {0: [...]} instead of [[...]]). orjson does not support non-string
    dict keys, so we normalise them here before serialisation.
    """
    if isinstance(obj, dict):
        return {str(k): _stringify_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_stringify_keys(item) for item in obj]
    return obj


class ConsultORJSONRenderer(ORJSONRenderer):
    def render(self, data: Any, accepted_media_type=None, renderer_context=None) -> bytes:
        return super().render(_stringify_keys(data), accepted_media_type, renderer_context)
