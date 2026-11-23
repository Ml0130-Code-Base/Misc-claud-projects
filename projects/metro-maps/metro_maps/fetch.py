"""Download MetroDreamin map view pages and store new snapshots."""

from __future__ import annotations

import base64
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

from . import snapshot_dir
from .model import SnapshotError, from_payload

BASE_URL = "https://metrodreamin.com/view/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) metro-maps snapshot script"
TIMEOUT_S = 30
PAUSE_S = 1.0

_NEXT_DATA = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>', re.S
)


class FetchError(Exception):
    pass


def map_id(user_id: str, index: int) -> str:
    """btoa('<userId>|<index>')"""
    return base64.b64encode(f"{user_id}|{index}".encode("utf-8")).decode("ascii")


def view_url(user_id: str, index: int) -> str:
    """encodeURIComponent of the ID, so '=' padding becomes %3D."""
    return BASE_URL + urllib.parse.quote(map_id(user_id, index), safe="")


def extract_next_data(html: str) -> dict:
    m = _NEXT_DATA.search(html)
    if not m:
        raise FetchError("page has no __NEXT_DATA__ script")
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise FetchError(f"__NEXT_DATA__ is not valid JSON ({e})") from None


def http_get(url: str) -> tuple[int, str]:
    """GET following redirects. Returns (status, body); raises FetchError on network errors."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise FetchError(f"network error: {getattr(e, 'reason', e)}") from None


def save_snapshot(root: Path, slug: str, payload: dict, last_updated: int) -> tuple[Path, bool]:
    """Write snapshots/<slug>/<lastUpdated>.json unless it exists. Returns (path, written)."""
    d = snapshot_dir(root, slug)
    path = d / f"{last_updated}.json"
    if path.exists():
        return path, False
    d.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(path)
    return path, True


def fetch_one(user_id: str, index: int, slug: str, root: Path,
              get: Callable[[str], tuple[int, str]] = http_get) -> str:
    """Fetch and store one map. Returns a status line; raises FetchError on failure."""
    url = view_url(user_id, index)
    status, body = get(url)
    if status != 200:
        raise FetchError(f"HTTP {status}")
    payload = extract_next_data(body)
    try:
        snap = from_payload(payload)
    except SnapshotError as e:
        raise FetchError(f"unexpected payload: {e}") from None
    path, written = save_snapshot(root, slug, payload, snap.last_updated)
    state = "new snapshot" if written else "unchanged"
    return (f"{slug} (#{index}): {state} {path.name} | {snap.title} | "
            f"{len(snap.real_stations)} stations, {len(snap.lines)} lines | updated {snap.updated_text}")


def fetch_all(config: dict, root: Path, only: set[str] | None = None,
              get: Callable[[str], tuple[int, str]] = http_get,
              sleep: Callable[[float], None] = time.sleep,
              out: Callable[[str], None] = print) -> int:
    """Fetch every configured map; one failure does not stop the rest. Returns exit code."""
    failed = 0
    maps = [m for m in config["maps"] if only is None or m["slug"] in only]
    for i, m in enumerate(maps):
        if i:
            sleep(PAUSE_S)
        try:
            out(fetch_one(config["userId"], m["index"], m["slug"], root, get))
        except FetchError as e:
            failed += 1
            out(f"{m['slug']} (#{m['index']}): FAILED {e}")
    return 1 if failed else 0
