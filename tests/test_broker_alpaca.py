import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import broker_alpaca as broker  # noqa: E402


@pytest.fixture(autouse=True)
def _creds(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY_ID", "key123")
    monkeypatch.setenv("ALPACA_API_SECRET_KEY", "secret456")


class FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_missing_credentials_raise(monkeypatch):
    monkeypatch.delenv("ALPACA_API_KEY_ID", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET_KEY", raising=False)
    with pytest.raises(broker.BrokerError):
        broker.get_account()


def test_base_url_is_hardcoded_to_paper():
    assert broker.PAPER_BASE_URL == "https://paper-api.alpaca.markets"
    assert "paper" in broker.PAPER_BASE_URL


def test_submit_order_hits_paper_endpoint_with_auth_headers():
    captured = {}

    def fake_urlopen(req, timeout=15):
        captured["url"] = req.full_url
        captured["headers"] = {k.lower(): v for k, v in req.headers.items()}
        captured["body"] = json.loads(req.data)
        return FakeResponse({"id": "order-1", "status": "accepted"})

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        result = broker.submit_order("xom", "buy", "50")

    assert captured["url"] == "https://paper-api.alpaca.markets/v2/orders"
    assert captured["headers"]["apca-api-key-id"] == "key123"
    assert captured["headers"]["apca-api-secret-key"] == "secret456"
    assert captured["body"] == {
        "symbol": "XOM", "qty": "50", "side": "buy", "type": "market", "time_in_force": "day",
    }
    assert result == {"id": "order-1", "status": "accepted"}


def test_submit_order_rejects_bad_side():
    with pytest.raises(broker.BrokerError):
        broker.submit_order("XOM", "hold", "50")


def test_limit_order_requires_limit_price():
    with pytest.raises(broker.BrokerError):
        broker.submit_order("XOM", "buy", "50", order_type="limit")


def test_limit_order_includes_price():
    captured = {}

    def fake_urlopen(req, timeout=15):
        captured["body"] = json.loads(req.data)
        return FakeResponse({"id": "order-2"})

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        broker.submit_order("XOM", "sell", "10", order_type="limit", limit_price="120.50")

    assert captured["body"]["type"] == "limit"
    assert captured["body"]["limit_price"] == "120.50"


def test_http_error_wrapped_as_broker_error():
    def fake_urlopen(req, timeout=15):
        raise urllib.error.HTTPError(req.full_url, 403, "forbidden", {}, None)

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        with pytest.raises(broker.BrokerError):
            broker.get_account()


def test_wait_for_terminal_polls_until_filled(monkeypatch):
    statuses = iter(["new", "pending_new", "filled"])
    calls = []

    def fake_get_order(order_id):
        status = next(statuses)
        calls.append(status)
        return {"id": order_id, "status": status}

    monkeypatch.setattr(broker, "get_order", fake_get_order)
    monkeypatch.setattr(broker.time, "sleep", lambda s: None)

    order = broker.wait_for_terminal("order-3", timeout_s=10, poll_s=0)

    assert order["status"] == "filled"
    assert calls == ["new", "pending_new", "filled"]


def test_cli_submit_prints_json(capsys):
    def fake_urlopen(req, timeout=15):
        return FakeResponse({"id": "order-4", "status": "accepted"})

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        rc = broker.main(["submit", "--symbol", "XOM", "--side", "buy", "--qty", "50"])

    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"id": "order-4", "status": "accepted"}


def test_cli_reports_error_on_stderr(capsys, monkeypatch):
    monkeypatch.delenv("ALPACA_API_KEY_ID", raising=False)
    rc = broker.main(["account"])
    assert rc == 1
    err = json.loads(capsys.readouterr().err)
    assert "ALPACA_API_KEY_ID" in err["error"]
