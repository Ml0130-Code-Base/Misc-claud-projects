"""Snapshot and analyze MetroDreamin fantasy transit maps."""

from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_config(root: Path = PROJECT_ROOT) -> dict:
    """Read maps.json: {"userId": str, "maps": [{"index": int, "slug": str}, ...]}."""
    with open(root / "maps.json", encoding="utf-8") as f:
        return json.load(f)


def snapshot_dir(root: Path, slug: str) -> Path:
    return root / "snapshots" / slug


def report_dir(root: Path, slug: str) -> Path:
    return root / "reports" / slug


def list_snapshots(root: Path, slug: str) -> list[Path]:
    """Snapshot files for a map, oldest first (named by lastUpdated epoch ms)."""
    d = snapshot_dir(root, slug)
    if not d.is_dir():
        return []
    files = [p for p in d.glob("*.json") if p.stem.isdigit()]
    return sorted(files, key=lambda p: int(p.stem))
