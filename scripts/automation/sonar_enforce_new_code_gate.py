#!/usr/bin/env python3
"""Fail CI when severe or security issues exist on Sonar new code."""

from __future__ import annotations

import json
import os
import time
from http.client import HTTPConnection, HTTPSConnection
import urllib.parse
from typing import Any


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _int_env(name: str, default: int) -> int:
    value = _env(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _build_api_base() -> str:
    explicit = _env("SONAR_API_BASE")
    if explicit:
        return explicit.rstrip("/")
    host = _env("SONAR_HOST_URL", "https://sonarcloud.io").rstrip("/")
    if host.endswith("/api"):
        return host
    return f"{host}/api"


SONAR_API_BASE = _build_api_base()
SONAR_TOKEN = _env("SONAR_TOKEN")
SONAR_PROJECT_KEY = _env("SONAR_PROJECT_KEY")
SONAR_BRANCH = _env("SONAR_BRANCH", "main")
SONAR_PULL_REQUEST = _env("SONAR_PULL_REQUEST")

CRITICAL_SEVERITIES = _env("SONAR_GATE_CRITICAL_SEVERITIES", "BLOCKER,CRITICAL")
SECURITY_TYPES = _env("SONAR_GATE_SECURITY_TYPES", "VULNERABILITY")

MAX_WAIT_SEC = _int_env("SONAR_GATE_MAX_WAIT_SEC", 180)
POLL_INTERVAL_SEC = _int_env("SONAR_GATE_POLL_INTERVAL_SEC", 10)


def _require_inputs() -> None:
    missing: list[str] = []
    if not SONAR_TOKEN:
        missing.append("SONAR_TOKEN")
    if not SONAR_PROJECT_KEY:
        missing.append("SONAR_PROJECT_KEY")
    if missing:
        print(
            "[warn] Sonar new-code gate skipped because required inputs are missing: "
            + ", ".join(missing)
        )
        raise SystemExit(0)


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {SONAR_TOKEN}",
        "Accept": "application/json",
        "User-Agent": "coffeestudio-sonar-new-code-gate",
    }


def _http_json(url: str, *, retries: int = 4, timeout: int = 45) -> Any:
    last_error: Exception | None = None
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError(f"Invalid Sonar API URL: {url}")

    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    for attempt in range(1, retries + 1):
        connection_cls = HTTPSConnection if parsed.scheme == "https" else HTTPConnection
        conn = connection_cls(parsed.netloc, timeout=timeout)
        try:
            conn.request("GET", path, headers=_headers())
            response = conn.getresponse()
            payload = response.read().decode("utf-8", "replace")
            if response.status >= 400:
                is_retryable = response.status in {
                    408,
                    409,
                    425,
                    429,
                    500,
                    502,
                    503,
                    504,
                }
                if attempt < retries and is_retryable:
                    time.sleep(min(2**attempt, 8))
                    continue
                raise RuntimeError(f"HTTP {response.status} for {url}: {payload}")
            return json.loads(payload)
        except (OSError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(2**attempt, 8))
                continue
            break
        finally:
            conn.close()
    raise RuntimeError(f"Failed to query Sonar API: {last_error}")


def _base_issue_params() -> dict[str, str]:
    params: dict[str, str] = {
        "componentKeys": SONAR_PROJECT_KEY,
        "resolved": "false",
        "inNewCodePeriod": "true",
        "ps": "1",
    }
    if SONAR_PULL_REQUEST:
        params["pullRequest"] = SONAR_PULL_REQUEST
    else:
        params["branch"] = SONAR_BRANCH
    return params


def _query_issue_total(extra_params: dict[str, str]) -> int:
    params = _base_issue_params()
    params.update(extra_params)
    url = f"{SONAR_API_BASE}/issues/search?{urllib.parse.urlencode(params)}"
    data = _http_json(url)
    total = data.get("total")
    if isinstance(total, int):
        return total
    paging = data.get("paging", {})
    if isinstance(paging, dict) and isinstance(paging.get("total"), int):
        return int(paging["total"])
    return 0


def _scope_description() -> str:
    if SONAR_PULL_REQUEST:
        return f"pull request #{SONAR_PULL_REQUEST}"
    return f"branch '{SONAR_BRANCH}'"


def main() -> int:
    _require_inputs()

    deadline = time.time() + max(MAX_WAIT_SEC, 0)
    last_error: Exception | None = None
    critical_issues = 0
    vulnerability_issues = 0

    while True:
        try:
            critical_issues = _query_issue_total({"severities": CRITICAL_SEVERITIES})
            vulnerability_issues = _query_issue_total({"types": SECURITY_TYPES})
            last_error = None
            break
        except Exception as exc:  # pragma: no cover - network dependent
            last_error = exc
            if time.time() >= deadline:
                break
            print(f"[warn] Sonar gate query not ready yet: {exc}")
            time.sleep(max(POLL_INTERVAL_SEC, 1))

    if last_error is not None:
        print(f"[error] Sonar new-code gate failed to query results: {last_error}")
        return 1

    print(
        "[info] Sonar new-code gate scope=%s critical_issues=%d vulnerability_issues=%d"
        % (_scope_description(), critical_issues, vulnerability_issues)
    )

    if critical_issues > 0 or vulnerability_issues > 0:
        print(
            "[error] Sonar gate failed: new code contains unresolved "
            "BLOCKER/CRITICAL or security issues."
        )
        print(
            "[hint] Inspect SonarCloud issues filtered by new code and fix before merge."
        )
        return 1

    print("[ok] Sonar new-code gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
