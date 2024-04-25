from unittest.mock import patch

import pytest
from django.test import Client


def test_404(client):
    resp = client.get("not/a/url")
    assert resp.status_code == 404
    assert b"If you typed the web address, check it is correct" in resp.content
