import json
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

SONAR_API_BASE = os.getenv("SONAR_API_BASE", "https://sonarcloud.io/api").rstrip("/")
SONAR_TOKEN = (os.getenv("SONAR_TOKEN") or "").strip()
PROJECT_KEY = (os.getenv("SONAR_PROJECT_KEY") or "").strip()

BRANCH = (os.getenv("SONAR_BRANCH") or "main").strip()
SEVERITIES = (os.getenv("SONAR_SEVERITIES") or "").strip()  # empty = all
STATUSES = (os.getenv("SONAR_STATUSES") or "OPEN,REOPENED,CONFIRMED").strip()
MAX_CREATE = int((os.getenv("SONAR_MAX_CREATE") or "30").strip())
AUTO_CLOSE = (os.getenv("SONAR_AUTO_CLOSE") or "false").strip().lower() == "true"
LABEL = (os.getenv("SONAR_LABEL") or "sonarcloud").strip()

GH_TOKEN = (os.getenv("GITHUB_TOKEN") or "").strip()
GH_REPO = (os.getenv("GITHUB_REPOSITORY") or "").strip()  # owner/repo

ISSUE_KEY_RE = re.compile(r"(?im)^\s*Sonar Issue Key:\s*([A-Za-z0-9_\-:]+)\s*$")


def http_json(url: str, headers: Dict[str, str], retries: int = 3) -> dict:
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 429 and attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code} for {url}\n{body}") from None
    raise RuntimeError("Failed after retries")


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
    try:
        gh_request("POST", f"/repos/{owner}/{repo}/labels", {"name": name, "color": "0e8a16"})
    except Exception:
        pass


def existing_mapping(owner: str, repo: str, label: str) -> Dict[str, Tuple[int, str]]:
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
    # SonarCloud recommends bearer authentication for Web API
    return {"Authorization": f"Bearer {SONAR_TOKEN}"}


def sonar_issue_url(issue_key: str) -> str:
    return f"https://sonarcloud.io/project/issues?id={urllib.parse.quote(PROJECT_KEY)}&open={urllib.parse.quote(issue_key)}"


def fetch_open() -> List[dict]:
    issues: List[dict] = []
    page, ps = 1, 100
    while True:
        params = {
            "projects": PROJECT_KEY,
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
        pi = int(paging.get("pageIndex", page))
        psz = int(paging.get("pageSize", ps))
        if pi * psz >= total:
            break
        page += 1
        if page > 200:
            break
    return issues


def truncate(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def mk_title(it: dict) -> str:
    sev = it.get("severity", "NA")
    typ = it.get("type", "ISSUE")
    msg = truncate(it.get("message", "Sonar issue"), 110)
    comp = truncate(it.get("component", ""), 60)
    line = it.get("line")
    loc = f"{comp}:{line}" if line else comp
    return truncate(f"Sonar [{sev}][{typ}] {msg} ({loc})", 180)


def mk_body(it: dict) -> str:
    key = it.get("key", "")
    return f"""## SonarCloud Issue

- **Project:** `{PROJECT_KEY}`
- **Key:** `{key}`
- **Severity:** `{it.get('severity','')}`
- **Type:** `{it.get('type','')}`
- **Status:** `{it.get('status','')}`
- **Rule:** `{it.get('rule','')}`
- **Component:** `{it.get('component','')}`
- **Line:** `{it.get('line','')}`

**Sonar Link:** {sonar_issue_url(key)}

Sonar Issue Key: {key}
"""


def main() -> int:
    if not SONAR_TOKEN:
        raise SystemExit("Missing SONAR_TOKEN (GitHub Secret).")
    if not PROJECT_KEY:
        raise SystemExit("Missing SONAR_PROJECT_KEY (GitHub Actions Variable).")
    if not GH_TOKEN or not GH_REPO:
        raise SystemExit("Missing GitHub token/repository context.")

    owner, repo = GH_REPO.split("/", 1)
    ensure_label(owner, repo, LABEL)
    existing = existing_mapping(owner, repo, LABEL)

    sonar_open = fetch_open()
    open_keys = {i.get("key") for i in sonar_open if i.get("key")}

    created = updated = skipped = 0

    for it in sonar_open:
        key = it.get("key")
        if not key:
            continue

        title = mk_title(it)
        body = mk_body(it)

        if key in existing:
            num, _state = existing[key]
            gh_request("PATCH", f"/repos/{owner}/{repo}/issues/{num}", {"title": title})
            updated += 1
            continue

        if created >= MAX_CREATE:
            skipped += 1
            continue

        gh_request(
            "POST",
            f"/repos/{owner}/{repo}/issues",
            {"title": title, "body": body, "labels": [LABEL]},
        )
        created += 1

    if AUTO_CLOSE:
        for key, (num, state) in existing.items():
            if state == "open" and key not in open_keys:
                gh_request("PATCH", f"/repos/{owner}/{repo}/issues/{num}", {"state": "closed"})

    print(f"Done. created={created} updated={updated} skipped={skipped} sonar_open={len(sonar_open)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
