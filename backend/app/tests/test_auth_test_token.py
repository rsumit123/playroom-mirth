import os

import pytest


def test_test_token_endpoint_disabled_in_prod(client, monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    r = client.post("/auth/test_token", json={"display_name": "Tester"})
    assert r.status_code == 404


def test_test_token_endpoint_creates_user_in_test_env(client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    r = client.post("/auth/test_token", json={"display_name": "TestPlayer"})
    assert r.status_code == 200
    body = r.json()
    assert "token" in body
    assert body["user"]["display_name"] == "TestPlayer"
