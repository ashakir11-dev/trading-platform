#!/usr/bin/env python3
"""Alpaca **paper-trading** order adapter.

Places and checks orders for forward testing. This is the only order-placing code in
the repository (see the hard rule in ``CLAUDE.md``): it is a plain script, not an MCP
tool or a subagent capability, so no stage/follow-up/evaluator agent can call it — only
the middleware, from ``/trade``, and only after the user has typed that command.

The base URL is **hard-coded to Alpaca's paper endpoint** and is not configurable by an
argument or environment variable: this script must never be able to reach a live
brokerage account. Forward testing only.

Credentials: ``ALPACA_API_KEY_ID`` / ``ALPACA_API_SECRET_KEY`` (a paper account's keys,
from the Alpaca dashboard). Nothing else is read from the environment.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

PAPER_BASE_URL = "https://paper-api.alpaca.markets"
TERMINAL_STATUSES = frozenset({
    "filled", "canceled", "expired", "rejected", "done_for_day", "replaced",
})


class BrokerError(RuntimeError):
    pass


def _credentials() -> tuple[str, str]:
    key_id = os.environ.get("ALPACA_API_KEY_ID")
    secret = os.environ.get("ALPACA_API_SECRET_KEY")
    if not key_id or not secret:
        raise BrokerError(
            "ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY must be set (paper account keys)."
        )
    return key_id, secret


def _request(method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    key_id, secret = _credentials()
    url = f"{PAPER_BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "APCA-API-KEY-ID": key_id,
        "APCA-API-SECRET-KEY": secret,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise BrokerError(f"Alpaca paper API {method} {path} -> {e.code}: {detail}") from e


def submit_order(symbol: str, side: str, qty: str, order_type: str = "market",
                  time_in_force: str = "day", limit_price: str | None = None) -> dict[str, Any]:
    if side not in ("buy", "sell"):
        raise BrokerError("side must be 'buy' or 'sell'")
    if order_type not in ("market", "limit"):
        raise BrokerError("order_type must be 'market' or 'limit'")
    body: dict[str, Any] = {
        "symbol": symbol.upper(),
        "qty": qty,
        "side": side,
        "type": order_type,
        "time_in_force": time_in_force,
    }
    if order_type == "limit":
        if not limit_price:
            raise BrokerError("limit_price is required for a limit order")
        body["limit_price"] = limit_price
    return _request("POST", "/v2/orders", body)


def get_order(order_id: str) -> dict[str, Any]:
    return _request("GET", f"/v2/orders/{order_id}")


def cancel_order(order_id: str) -> None:
    _request("DELETE", f"/v2/orders/{order_id}")


def list_positions() -> Any:
    return _request("GET", "/v2/positions")


def get_account() -> dict[str, Any]:
    return _request("GET", "/v2/account")


def wait_for_terminal(order_id: str, timeout_s: int, poll_s: float = 2.0) -> dict[str, Any]:
    """Poll an order until it reaches a terminal status or ``timeout_s`` elapses."""
    deadline = time.monotonic() + timeout_s
    order = get_order(order_id)
    while order.get("status") not in TERMINAL_STATUSES and time.monotonic() < deadline:
        time.sleep(poll_s)
        order = get_order(order_id)
    return order


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    submit = sub.add_parser("submit", help="Submit a paper order")
    submit.add_argument("--symbol", required=True)
    submit.add_argument("--side", required=True, choices=["buy", "sell"])
    submit.add_argument("--qty", required=True)
    submit.add_argument("--type", dest="order_type", default="market", choices=["market", "limit"])
    submit.add_argument("--tif", dest="time_in_force", default="day")
    submit.add_argument("--limit-price")
    submit.add_argument("--wait", type=int, default=0,
                         help="Seconds to poll for a terminal status before returning")

    status = sub.add_parser("status", help="Get one order")
    status.add_argument("order_id")

    cancel = sub.add_parser("cancel", help="Cancel one order")
    cancel.add_argument("order_id")

    sub.add_parser("positions", help="List open paper positions")
    sub.add_parser("account", help="Paper account summary")
    return p


def main(argv: list[str]) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "submit":
            order = submit_order(args.symbol, args.side, args.qty, args.order_type,
                                  args.time_in_force, args.limit_price)
            if args.wait > 0 and order.get("id"):
                order = wait_for_terminal(order["id"], args.wait)
            result: Any = order
        elif args.command == "status":
            result = get_order(args.order_id)
        elif args.command == "cancel":
            cancel_order(args.order_id)
            result = {"canceled": args.order_id}
        elif args.command == "positions":
            result = list_positions()
        elif args.command == "account":
            result = get_account()
        else:  # pragma: no cover - argparse enforces the choices above
            raise BrokerError(f"unknown command {args.command}")
    except BrokerError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
