from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teacher.providers import http as provider_http  # noqa: E402


def test_create_ssl_context_uses_certifi_bundle(monkeypatch) -> None:
    sentinel_context = object()
    captured: dict[str, Any] = {}

    monkeypatch.setattr(provider_http.certifi, "where", lambda: "/tmp/cacert.pem")

    def _fake_create_default_context(
        *,
        cafile: str | None = None,
        capath: str | None = None,
        cadata: str | None = None,
    ) -> object:
        captured["cafile"] = cafile
        captured["capath"] = capath
        captured["cadata"] = cadata
        return sentinel_context

    monkeypatch.setattr(provider_http.ssl, "create_default_context", _fake_create_default_context)

    context = provider_http.create_ssl_context()

    assert context is sentinel_context
    assert captured["cafile"] == "/tmp/cacert.pem"
    assert captured["capath"] is None
    assert captured["cadata"] is None


def test_http_json_post_passes_ssl_context_to_urlopen(monkeypatch) -> None:
    sentinel_context = object()
    captured: dict[str, Any] = {}

    monkeypatch.setattr(provider_http, "create_ssl_context", lambda: sentinel_context)

    class _FakeResponse:
        status = 200

        def __enter__(self) -> _FakeResponse:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"ok": True}).encode("utf-8")

    def _fake_urlopen(req, timeout, context):  # type: ignore[no-untyped-def]
        captured["req"] = req
        captured["timeout"] = timeout
        captured["context"] = context
        return _FakeResponse()

    monkeypatch.setattr(provider_http.request, "urlopen", _fake_urlopen)

    status, payload, body = provider_http.http_json_post(
        provider="test_provider",
        url="https://example.test/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        payload={"hello": "world"},
        timeout_seconds=12.5,
    )

    assert status == 200
    assert payload == {"ok": True}
    assert body == '{"ok": true}'
    assert captured["timeout"] == 12.5
    assert captured["context"] is sentinel_context
