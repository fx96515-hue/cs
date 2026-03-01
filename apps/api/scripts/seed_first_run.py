"""Seed discovery for cooperatives/roasters using Perplexity.

Usage (inside docker):
  docker compose exec backend python scripts/seed_first_run.py --coops --max 50
  docker compose exec backend python scripts/seed_first_run.py --roasters --max 100
  docker compose exec backend python scripts/seed_first_run.py --both --max 50 --dry-run

Requires:
  PERPLEXITY_API_KEY (env)
"""

from __future__ import annotations

import os
import sys
import argparse
import json

# Ensure /app is on sys.path so `import app` works when running from /app/scripts.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


from app.db.session import SessionLocal  # noqa: E402
from app.services.discovery import seed_discovery  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--coops", action="store_true", help="Seed cooperatives (Peru)")
    p.add_argument("--roasters", action="store_true", help="Seed roasters (Germany)")
    p.add_argument("--both", action="store_true", help="Seed both")
    p.add_argument("--max", type=int, default=100, help="Max entities per type")
    p.add_argument("--dry-run", action="store_true", help="Do not persist")
    p.add_argument(
        "--country", type=str, default=None, help="Override country filter (PE|DE)"
    )
    args = p.parse_args()

    if not (args.coops or args.roasters or args.both):
        p.error("Choose one of --coops/--roasters/--both")

    db = SessionLocal()
    try:
        out = {}
        if args.both or args.coops:
            out["cooperatives"] = seed_discovery(
                db,
                entity_type="cooperative",
                max_entities=args.max,
                dry_run=args.dry_run,
                country_filter=args.country,
            )
        if args.both or args.roasters:
            out["roasters"] = seed_discovery(
                db,
                entity_type="roaster",
                max_entities=args.max,
                dry_run=args.dry_run,
                country_filter=args.country,
            )

        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
