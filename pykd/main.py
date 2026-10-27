from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .database import Database


DEFAULT_DATABASE_PATH = Path("data/pykd.db")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pykd",
        description="PyKD Mk1 - Python Key-Value Database Engine",
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Path to the PyKD database file",
    )

    return parser


def run(database_path: Path) -> int:
    database_path.parent.mkdir(parents=True, exist_ok=True)

    database = Database(database_path)

    try:
        database.open()

        from .cli import CommandLine

        cli = CommandLine(database)
        cli.start()

        return 0

    except KeyboardInterrupt:
        print("\nPyKD shutting down.")
        return 0

    except Exception as exc:
        print(f"PyKD error: {exc}", file=sys.stderr)
        return 1

    finally:
        database.close()


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    return run(args.db)


if __name__ == "__main__":
    raise SystemExit(main())