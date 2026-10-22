"""Tests for the Langfuse dataset migration utility."""

from unittest.mock import Mock

from components import COMPONENT_NAMES

from scripts import migrate_to_langfuse


def test_migrate_all_uses_registered_components(monkeypatch):
    client = Mock()
    migrated = []

    monkeypatch.setattr(migrate_to_langfuse, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(
        migrate_to_langfuse,
        "migrate_component",
        lambda actual_client, dataset, component: migrated.append(
            (actual_client, dataset, component)
        ),
    )

    migrate_to_langfuse.migrate_all("demo")

    assert migrated == [(client, "demo", component) for component in COMPONENT_NAMES]
    client.flush.assert_called_once_with()
