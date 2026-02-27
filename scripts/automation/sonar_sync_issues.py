from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


SONAR_API_BASE = (os.getenv("SONAR_API_BASE") or "https://sonarcloud.io/api").rstrip("/")
SONAR_TOKEN = (os.getenv("SONAR_TOKEN") or "").strip()

PROJECT_KEY = (os.getenv("SONAR_PROJECT_KEY") or "").strip()
BRANCH = (os.getenv("SONAR_BRANCH") or "main").strip()

SEVERITIES = (os.getenv("SONAR_SEVERITIES") or "").strip()
STATUSES = (os.getenv("SONAR_STATUSES") or "OPEN,REOPENED,CONFIRMED").strip()

MAX_CREATE = int((os.getenv("SONAR_MAX_CREATE") or "30").strip())
AUTO_CLOSE = (os.getenv("SONAR_AUTO_CLOSE") or "false").strip().lower() == "true"
LABEL = (os.getenv("SONAR_LABEL") or "sonarcloud").strip()

GH_TOKEN = (os.getenv("GITHUB_TOKEN") or "").strip()
GH_REPO = (os.getenv("GITHUB_REPOSITORY") or "").strip()  # owner/repo

# Marker used to map Sonar issue -> GitHub issue.
ISSUE_KEY_RE = re.compile(r"(?im)^\s*Sonar Issue Key:\s*([A-Za-z0-9_\-:]+)\s*$")


@dataclass(frozen=True)
class GhIssueRef:
    number: int
    state: str
    title: str
    body: str


def _require_env() -> None:
    missing = []
    if not SONAR_TOKEN:
        missing.append("SONAR_TOKEN (GitHub Secret)")
    if not PROJECT_KEY:
        missing.append("SONAR_PROJECT_KEY (GitHub Variable)")
    if not GH_TOKEN:
        missing.append("GITHUB_TOKEN (workflow context)")
    if not GH_REPO:
        missing.append("GITHUB_REPOSITORY (workflow context)")
    if missing:
        raise SystemExit("Missing required env: " + ", ".join(missing))


def _http_json(
    url: str,
    *,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Dict[str, Any]] = None,
    retries: int = 4,
    timeout: int = 60,
) -> Any:
    hdrs = dict(headers or {})

    for attempt in range(retries):
        try:
            response = httpx.request(
                method,
                url,
                headers=hdrs,
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            if not response.text:
                return {}
            return response.json()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            body = e.response.text
            # Rate limiting / transient
            if status in (429, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {status} for {url}\n{body}") from None
        except httpx.RequestError as e:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise RuntimeError(f"Network error for {url}: {e}") from None

    raise RuntimeError("Failed after retries")


def _gh_api_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "coffeestudio-sonar-issues-sync",
    }


def _sonar_headers() -> Dict[str, str]:
    # SonarCloud supports bearer auth for Web API
    return {"Authorization": f"Bearer {SONAR_TOKEN}"}


def _gh_request(method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    url = f"https://api.github.com{path}"
    return _http_json(
        url,
        method=method,
        headers=_gh_api_headers(),
        payload=payload,
        retries=4,
        timeout=60,
    )


def _gh_paginate(path: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    page = 1
    while True:
        sep = "&" if "?" in path else "?"
        url = f"https://api.github.com{path}{sep}per_page=100&page={page}"
        chunk = _http_json(url, headers=_gh_api_headers(), retries=4, timeout=60)
        if not isinstance(chunk, list) or not chunk:
            break
        out.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
        if page > 50:
            break
    return out


def _ensure_label(owner: str, repo: str, name: str) -> None:
    try:
        _gh_request("POST", f"/repos/{owner}/{repo}/labels", {"name": name, "color": "0e8a16"})
    except Exception:
        # Already exists or no permission—ignore.
        return


def _extract_key(body: str) -> Optional[str]:
    m = ISSUE_KEY_RE.search(body or "")
    return m.group(1) if m else None


def _existing_mapping(owner: str, repo: str, label: str) -> Dict[str, GhIssueRef]:
    items = _gh_paginate(f"/repos/{owner}/{repo}/issues?state=all&labels={urllib.parse.quote(label)}")
    mapping: Dict[str, GhIssueRef] = {}

    # Deduplicate: keep the lowest issue number per sonar key.
    dups: Dict[str, List[int]] = {}

    for it in items:
        if "pull_request" in it:
            continue
        body = it.get("body") or ""
        key = _extract_key(body)
        if not key:
            continue

        ref = GhIssueRef(
            number=int(it["number"]),
            state=str(it.get("state", "open")),
            title=str(it.get("title", "")),
            body=str(body),
        )

        if key in mapping:
            keep = mapping[key]
            if ref.number < keep.number:
                dups.setdefault(key, []).append(keep.number)
                mapping[key] = ref
            else:
                dups.setdefault(key, []).append(ref.number)
        else:
            mapping[key] = ref

    for key, nums in dups.items():
        nums_sorted = sorted(nums)
        print(f"[warn] Duplicate GitHub issues for Sonar key {key}: extra={nums_sorted}, kept={mapping[key].number}")

    return mapping


def _sonar_issue_link(issue_key: str) -> str:
    return (
        "https://sonarcloud.io/project/issues?"
        + urllib.parse.urlencode({"id": PROJECT_KEY, "open": issue_key})
    )


def _sonar_search_open() -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    page = 1
    page_size = 100

    while True:
        params: Dict[str, str] = {
            "projects": PROJECT_KEY,
            "branch": BRANCH,
            "statuses": STATUSES,
            "ps": str(page_size),
            "p": str(page),
        }
        if SEVERITIES:
            params["severities"] = SEVERITIES

        url = f"{SONAR_API_BASE}/issues/search?{urllib.parse.urlencode(params)}"
        data = _http_json(url, headers=_sonar_headers(), retries=4, timeout=60) or {}
        chunk = data.get("issues") or []
        issues.extend(chunk)

        paging = data.get("paging") or {}
        total = int(paging.get("total", 0))
        page_index = int(paging.get("pageIndex", page))
        psz = int(paging.get("pageSize", page_size))

        if page_index * psz >= total:
            break

        page += 1
        if page > 200:
            break

    return issues


def _truncate(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _mk_title(it: Dict[str, Any]) -> str:
    sev = it.get("severity", "NA")
    typ = it.get("type", "ISSUE")
    msg = _truncate(it.get("message", "Sonar issue"), 110)
    comp = _truncate(it.get("component", ""), 60)
    line = it.get("line")
    loc = f"{comp}:{line}" if line else comp
    return _truncate(f"Sonar [{sev}][{typ}] {msg} ({loc})", 180)


def _mk_body(it: Dict[str, Any]) -> str:
    key = str(it.get("key", "") or "").strip()
    rule = str(it.get("rule", "") or "").strip()
    comp = str(it.get("component", "") or "").strip()
    line = str(it.get("line", "") or "").strip()
    msg = str(it.get("message", "") or "").strip()
    sev = str(it.get("severity", "") or "").strip()
    typ = str(it.get("type", "") or "").strip()
    status = str(it.get("status", "") or "").strip()

    link = _sonar_issue_link(key) if key else "n/a"

    # Keep a stable marker line for mapping + future dedupe.
    return "\n".join(
        [
            "## SonarCloud Issue",
            f"- **Project:** `{PROJECT_KEY}`",
            f"- **Key:** `{key}`",
            f"- **Severity:** `{sev}`",
            f"- **Type:** `{typ}`",
            f"- **Status:** `{status}`",
            f"- **Rule:** `{rule}`",
            f"- **Component:** `{comp}`",
            f"- **Line:** `{line}`",
            "",
            f"**Message:** {msg}",
            "",
            f"**Sonar Link:** {link}",
            "",
            f"Sonar Issue Key: {key}",
        ]
    )


def _needs_update(existing: GhIssueRef, new_title: str, new_body: str) -> bool:
    if (existing.title or "").strip() != (new_title or "").strip():
        return True
    if (existing.body or "").strip() != (new_body or "").strip():
        return True
    return False


def _sync_open_issues(
    *,
    owner: str,
    repo: str,
    existing: Dict[str, GhIssueRef],
    sonar_open: List[Dict[str, Any]],
) -> tuple[int, int, int]:
    created = 0
    updated = 0
    skipped = 0

    for it in sonar_open:
        key = str(it.get("key") or "").strip()
        if not key:
            continue

        title = _mk_title(it)
        body = _mk_body(it)

        if key in existing:
            ref = existing[key]
            if _needs_update(ref, title, body):
                _gh_request(
                    "PATCH",
                    f"/repos/{owner}/{repo}/issues/{ref.number}",
                    {"title": title, "body": body},
                )
                updated += 1
            continue

        if created >= MAX_CREATE:
            skipped += 1
            continue

        _gh_request(
            "POST",
            f"/repos/{owner}/{repo}/issues",
            {"title": title, "body": body, "labels": [LABEL]},
        )
        created += 1

    return created, updated, skipped


def _auto_close_issues(
    *,
    owner: str,
    repo: str,
    existing: Dict[str, GhIssueRef],
    open_keys: set[str],
) -> int:
    if not AUTO_CLOSE or not existing:
        return 0

    closed = 0
    for key, ref in existing.items():
        if ref.state == "open" and key not in open_keys:
            _gh_request(
                "PATCH",
                f"/repos/{owner}/{repo}/issues/{ref.number}",
                {"state": "closed"},
            )
            closed += 1

    return closed


def main() -> int:
    _require_env()
    owner, repo = GH_REPO.split("/", 1)

    _ensure_label(owner, repo, LABEL)

    existing = _existing_mapping(owner, repo, LABEL)
    sonar_open = _sonar_search_open()
    open_keys = {str(i.get("key")) for i in sonar_open if i.get("key")}
    created, updated, skipped = _sync_open_issues(
        owner=owner,
        repo=repo,
        existing=existing,
        sonar_open=sonar_open,
    )
    closed = _auto_close_issues(
        owner=owner,
        repo=repo,
        existing=existing,
        open_keys=open_keys,
    )

    print(
        "Done. "
        f"created={created} updated={updated} skipped={skipped} "
        f"sonar_open={len(sonar_open)} auto_close={AUTO_CLOSE} closed={closed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
