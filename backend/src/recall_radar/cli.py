"""Command line: `uv run recall-radar --help`

recall-radar seed ../research/api-exploration/data/samples   # load the saved API samples
recall-radar ingest cpsc --days 30                          # pull live data once
"""

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

from recall_radar.config import get_settings
from recall_radar.db import SessionLocal
from recall_radar.ingest.run import ingest
from recall_radar.ingest.samples import load_samples
from recall_radar.log_config import configure_logging
from recall_radar.models import RecallSource


def main() -> None:
    parser = argparse.ArgumentParser(prog="recall-radar")
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed", help="Load saved sample payloads into the database")
    seed.add_argument("samples_dir", type=Path)

    pull = sub.add_parser("ingest", help="Pull recent recalls from one agency")
    pull.add_argument("source", choices=[s.value for s in RecallSource])
    pull.add_argument("--days", type=int, default=7)

    args = parser.parse_args()
    configure_logging(get_settings().log_level)

    with SessionLocal() as db:
        if args.command == "seed":
            result = load_samples(db, args.samples_dir)
            print(
                f"seeded: {result.new} new, {result.updated} updated, {result.unchanged} unchanged"
            )
        elif args.command == "ingest":
            end = datetime.now(UTC).date()
            run = ingest(db, RecallSource(args.source), end - timedelta(days=args.days), end)
            print(
                f"{args.source}: fetched {run.fetched}, {run.new_recalls} new, "
                f"{run.updated_recalls} updated, {run.errors} errors"
            )


if __name__ == "__main__":
    main()
