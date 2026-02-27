import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

SONAR_API_BASE = os.getenv("SONAR_API_BASE", "https://sonarcloud.io/api").rstrip("/")
SONAR_TOKEN = os.getenv("SONAR_TOKEN", "").strip()
PROJECT_KEY = os.getenv("SONAR_PROJECT_KEY", "").strip()

BRANCH = (os.getenv("SONAR_BRANCH") or "main").strip()
SEVERITIES = (os.getenv("SONAR_SEVERITIES") or "").strip()  # empty = all
STATUSES = (os.getenv("SONAR_STATUSES") or "OPEN,REOPENED,CONFIRMED").strip()
MAX_CREATE = int((os.getenv("SONAR_MAX_CREATE") or "30").strip())
AUTO_CLOSE = (os.getenv("SONAR_AUTO_CLOSE") or "false").strip().lower() == "true"
LABEL = (os.getenv("SONAR_LABEL") or "sonarcloud").strip()

GH_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GH_REPO = os.getenv("GITHUB_REPOSITORY", "").strip()  # owner/repo

ISSUE_KEY_RE = re.compile(r"(?im)^\s*Sonar Issue Key:\s*([A-Za-z0-9_\-:]+)\s*$")

def http_json(url: str, headers: Dict[str, str], retries: int = 3) -> dict:
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read().decode("utf-8", errors="replace")
                return json.loads(data)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 429 and attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code} for {url}\n{body}") from None
    raise RuntimeError(f"Failed after retries for {url}")

def gh_request(method: str, path: str, payload: Optional[dict] = None) -> dict:
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "sonar-issues-sync",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        out = resp.read().decode("utf-8", errors="replace")
        return json.loads(out) if out else {}

def gh_paginate(path: str) -> List[dict]:
    # Simple page-based pagination for /issues listing
    out: List[dict] = []
    page = 1
    while True:
        p = f"{path}&per_page=100&page={page}" if "?" in path else f"{path}?per_page=100&page={page}"
        url = f"https://api.github.com{p}"
        headers = {
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "sonar-issues-sync",
        }
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=60) as resp:
            chunk = json.loads(resp.read().decode("utf-8", errors="replace") or "[]")
        if not chunk:
            break
        out.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return out

def ensure_label(owner: str, repo: str, name: str) -> None:
    # Create label if missing. Ignore if already exists.
    try:
        gh_request("POST", f"/repos/{owner}/{repo}/labels", {"name": name, "color": "0e8a16"})
    except Exception:
        # could be 422 already exists or permissions; safe to ignore
        pass

def get_existing_sonar_issues(owner: str, repo: str, label: str) -> Dict[str, Tuple[int, str]]:
    items = gh_paginate(f"/repos/{owner}/{repo}/issues?state=all&labels={urllib.parse.quote(label)}")
    mapping: Dict[str, Tuple[int, str]] = {}
    for it in items:
        if "pull_request" in it:
            continue
        body = it.get("body") or ""
        m = ISSUE_KEY_RE.search(body)
        if m:
            mapping[m.group(1)] = (int(it["number"]), it.get("state", "open"))
    return mapping

def sonar_headers() -> Dict[str, str]:
    # SonarCloud recommends Bearer auth. :contentReference[oaicite:3]{index=3}
    return {"Authorization": f"Bearer {SONAR_TOKEN}"}

def sonar_issue_url(issue_key: str) -> str:
    # Reliable linking format. :contentReference[oaicite:4]{index=4}
    return f"https://sonarcloud.io/project/issues?id={urllib.parse.quote(PROJECT_KEY)}&open={urllib.parse.quote(issue_key)}"

def fetch_sonar_issues_open() -> List[dict]:
    if not PROJECT_KEY:
        return []

    issues: List[dict] = []
    page = 1
    ps = 100
    # SonarCloud issues/search has 10k cap; keep filters tight if needed. :contentReference[oaicite:5]{index=5}
    while True:
        params = {
            "projects": PROJECT_KEY,     # 'projects' is accepted; 'projectKeys' is deprecated in some contexts.
            "branch": BRANCH,
            "statuses": STATUSES,
            "ps": str(ps),
            "p": str(page),
        }
        if SEVERITIES:
            params["severities"] = SEVERITIES

        url = f"{SONAR_API_BASE}/issues/search?{urllib.parse.urlencode(params)}"
        data = http_json(url, headers=sonar_headers())

        chunk = data.get("issues") or []
        issues.extend(chunk)

        paging = data.get("paging") or {}
        total = int(paging.get("total", 0))
        page_index = int(paging.get("pageIndex", page))
        page_size = int(paging.get("pageSize", ps))

        if page_index * page_size >= total:
            break
        page += 1

        if page > 200:  # hard guard
            break

    return issues

def truncate(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"

def mk_title(issue: dict) -> str:
    sev = issue.get("severity", "NA")
    typ = issue.get("type", "ISSUE")
    msg = truncate(issue.get("message", "Sonar issue"), 110)
    comp = issue.get("component", "")
    line = issue.get("line")
    loc = f"{comp}:{line}" if line else comp
    loc = truncate(loc, 60)
    return truncate(f"Sonar [{sev}][{typ}] {msg} ({loc})", 180)

def mk_body(issue: dict) -> str:
    key = issue.get("key", "")
    rule = issue.get("rule", "")
    sev = issue.get("severity", "")
    typ = issue.get("type", "")
    comp = issue.get("component", "")
    line = issue.get("line", "")
    status = issue.get("status", "")
    created = issue.get("creationDate", "")
    updated = issue.get("updateDate", "")
    url = sonar_issue_url(key)

    return f"""## SonarCloud Issue

- **Project:** `{PROJECT_KEY}`
- **Key:** `{key}`
- **Severity:** `{sev}`
- **Type:** `{typ}`
- **Status:** `{status}`
- **Rule:** `{rule}`
- **Component:** `{comp}`
- **Line:** `{line}`
- **Created:** `{created}`
- **Updated:** `{updated}`

**Sonar Link:** {url}

Sonar Issue Key: {key}
"""

def main() -> int:
    if not SONAR_TOKEN or not PROJECT_KEY or not GH_TOKEN or not GH_REPO:
        print("Sonar/GitHub not configured (missing SONAR_TOKEN / SONAR_PROJECT_KEY / GITHUB_TOKEN). Skipping.")
        return 0

    owner, repo = GH_REPO.split("/", 1)

    ensure_label(owner, repo, LABEL)
    existing = get_existing_sonar_issues(owner, repo, LABEL)

    sonar_open = fetch_sonar_issues_open()
    open_keys = {i.get("key") for i in sonar_open if i.get("key")}

    created = 0
    updated = 0
    skipped = 0

    for it in sonar_open:
        key = it.get("key")
        if not key:
            continue

        title = mk_title(it)
        body = mk_body(it)

        if key in existing:
            # Minimal update: keep it in sync (title/body) if needed
            number, _state = existing[key]
            # We won't fetch existing body to compare (extra calls). Just patch title.
            gh_request("PATCH", f"/repos/{owner}/{repo}/issues/{number}", {"title": title})
            updated += 1
            continue

        if created >= MAX_CREATE:
            skipped += 1
            continue

        payload = {
            "title": title,
            "body": body,
            "labels": [LABEL],
        }
        gh_request("POST", f"/repos/{owner}/{repo}/issues", payload)
        created += 1

    # Optional: auto-close GitHub issues that are open but no longer open in Sonar
    if AUTO_CLOSE:
        for key, (num, state) in list(existing.items()):
            if state != "open":
                continue
            if key in open_keys:
                continue
            gh_request("PATCH", f"/repos/{owner}/{repo}/issues/{num}", {"state": "closed"})
        print("AUTO_CLOSE enabled: closed GitHub issues that are no longer open in Sonar (best-effort).")

    print(f"Done. created={created}, updated={updated}, skipped_due_to_limit={skipped}, existing={len(existing)}, sonar_open={len(sonar_open)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
