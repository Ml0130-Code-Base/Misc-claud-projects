"""CLI: python -m metro_maps <fetch|diff|analyze> ..."""

import argparse
import sys
from pathlib import Path

from . import PROJECT_ROOT, list_snapshots, load_config


def _slugs(config: dict) -> list[str]:
    return [m["slug"] for m in config["maps"]]


def cmd_fetch(args, config) -> int:
    from .fetch import fetch_all

    wanted = set(args.maps) if args.maps else None
    unknown = (wanted or set()) - set(_slugs(config))
    if unknown:
        print(f"Unknown map(s): {', '.join(sorted(unknown))}. Known: {', '.join(_slugs(config))}")
        return 2
    return fetch_all(config, PROJECT_ROOT, only=wanted)


def cmd_diff(args, config) -> int:
    from .diff import diff_files

    if args.old or args.new:
        if not (args.old and args.new):
            print("Pass both --old and --new, or neither.")
            return 2
        old, new = Path(args.old), Path(args.new)
    else:
        snaps = list_snapshots(PROJECT_ROOT, args.map)
        if len(snaps) < 2:
            print(f"{args.map}: need two snapshots to diff, found {len(snaps)}.")
            return 1
        old, new = snaps[-2], snaps[-1]
    print(diff_files(old, new))
    return 0


def cmd_analyze(args, config) -> int:
    from .analyze import analyze_file

    if args.snapshot:
        snap = Path(args.snapshot)
    else:
        snaps = list_snapshots(PROJECT_ROOT, args.map)
        if not snaps:
            print(f"{args.map}: no snapshots yet. Run: python -m metro_maps fetch {args.map}")
            return 1
        snap = snaps[-1]
    out_path, text = analyze_file(snap, PROJECT_ROOT, args.map)
    print(text)
    print(f"\n(written to {out_path})", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    p = argparse.ArgumentParser(prog="python -m metro_maps", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    f = sub.add_parser("fetch", help="download configured maps and save new snapshots")
    f.add_argument("maps", nargs="*", help="map slugs from maps.json (default: all)")

    d = sub.add_parser("diff", help="compare two snapshots of a map")
    d.add_argument("map", help="map slug")
    d.add_argument("--old", help="older snapshot file (default: second most recent)")
    d.add_argument("--new", help="newer snapshot file (default: most recent)")

    a = sub.add_parser("analyze", help="write a punch list for a snapshot")
    a.add_argument("map", help="map slug")
    a.add_argument("--snapshot", help="snapshot file (default: most recent)")

    args = p.parse_args(argv)
    config = load_config()
    if getattr(args, "map", None) and args.map not in _slugs(config):
        print(f"Unknown map: {args.map}. Known: {', '.join(_slugs(config))}")
        return 2
    return {"fetch": cmd_fetch, "diff": cmd_diff, "analyze": cmd_analyze}[args.command](args, config)


if __name__ == "__main__":
    sys.exit(main())
