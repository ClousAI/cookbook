"""
Tiny, dependency-light helper shared by the cookbook recipes.

It wraps the Clous REST API (https://api.clous.ai):

  - reads CLOUS_API_KEY from the environment
  - sends the Bearer token
  - unwraps the standard response envelope
    {data[], page{limit,next_cursor,has_more}, as_of, source, query_echo, warnings}
  - follows cursor pagination for you

Only dependency: requests (see requirements.txt). Copy this file into your own
project, or import it from the recipe scripts (they add this folder to sys.path).
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, Iterator, List, Optional

import requests

BASE_URL = os.environ.get("CLOUS_BASE_URL", "https://api.clous.ai")


def api_key() -> str:
    key = os.environ.get("CLOUS_API_KEY")
    if not key:
        sys.exit(
            "CLOUS_API_KEY is not set.\n"
            "  Get a key at https://clous.ai and run:\n"
            "    export CLOUS_API_KEY=clous_live_...   (macOS/Linux)\n"
            '    $env:CLOUS_API_KEY="clous_live_..."   (PowerShell)'
        )
    return key


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key()}",
        "Accept": "application/json",
    }


def get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """GET an endpoint and return the full envelope (dict). Raises on HTTP error."""
    # drop None-valued params so we never send `?cik=None`
    clean = {k: v for k, v in (params or {}).items() if v is not None}
    resp = requests.get(f"{BASE_URL}{path}", headers=_headers(), params=clean, timeout=60)
    _raise_for_status(resp)
    return resp.json()


def post(path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """POST JSON to an endpoint and return the parsed response."""
    resp = requests.post(
        f"{BASE_URL}{path}",
        headers={**_headers(), "Content-Type": "application/json"},
        json=body,
        timeout=120,
    )
    _raise_for_status(resp)
    return resp.json()


def get_data(path: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """GET and return just the `data` array of one page."""
    return get(path, params).get("data", [])


def paginate(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    max_items: Optional[int] = None,
) -> Iterator[Dict[str, Any]]:
    """
    Yield records across pages by following page.next_cursor until has_more is
    false (or max_items is reached). This is the canonical cursor-pagination loop.
    """
    params = dict(params or {})
    seen = 0
    while True:
        env = get(path, params)
        for row in env.get("data", []):
            yield row
            seen += 1
            if max_items is not None and seen >= max_items:
                return
        page = env.get("page") or {}
        cursor = page.get("next_cursor")
        if not page.get("has_more") or not cursor:
            return
        params["cursor"] = cursor


def _raise_for_status(resp: requests.Response) -> None:
    if resp.status_code < 400:
        return
    detail = ""
    try:
        detail = resp.json().get("detail") or resp.text
    except Exception:
        detail = resp.text
    hints = {
        401: "Invalid or missing API key. Check CLOUS_API_KEY.",
        402: "Out of credits. Top up your plan at https://clous.ai.",
        422: "Validation error — a parameter was the wrong type or out of range.",
        429: "Rate limited. Back off and retry.",
    }
    hint = hints.get(resp.status_code, "")
    raise SystemExit(f"HTTP {resp.status_code} for {resp.url}\n  {hint}\n  {detail}")
