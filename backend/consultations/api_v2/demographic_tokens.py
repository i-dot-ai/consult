"""Opaque v2 demographic option tokens.

The responses demographic-options aggregation endpoint returns option `id`s as
tokens so the frontend can pass them straight back in the `?demographics=` filter
param without knowing the structure. A token carries the demographic question id
and the answer value it represents.
"""

import base64
import json
from uuid import UUID


def encode_demographic_token(question_id: UUID | str, value: str) -> str:
    """Encode (question_id, value) into an opaque, URL-safe token."""
    payload = json.dumps({"q": str(question_id), "v": value}, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_demographic_token(token: str) -> tuple[str, str] | None:
    """Decode a token back to (question_id, value); None when malformed."""
    try:
        padded = token + "=" * (-len(token) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
        question_id, value = payload["q"], payload["v"]
    except (ValueError, KeyError, TypeError):
        # binascii.Error subclasses ValueError; malformed tokens are ignored
        return None
    if not isinstance(question_id, str) or not isinstance(value, str):
        return None
    return question_id, value
