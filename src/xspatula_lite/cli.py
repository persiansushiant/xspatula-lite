from __future__ import annotations

import argparse

from xspatula_lite.core import Xspatula


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xspatula-lite")
    parser.add_argument("--scheme", required=True, help="Path to scheme JSON")
    parser.add_argument("--real-db", action="store_true", help="Disable mock mode. Not implemented yet.")
    sub = parser.add_subparsers(dest="command", required=True)

    job = sub.add_parser("run-job")
    job.add_argument("job_name")

    proc = sub.add_parser("run-process")
    proc.add_argument("process")

    pilot = sub.add_parser("run-pilot")
    pilot.add_argument("pilot_path")
    pilot.add_argument("--process-folder")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    xp = Xspatula(mock=not args.real_db)
    xp.load_scheme(args.scheme)
    if args.command == "run-job":
        xp.run_job(args.job_name)
    elif args.command == "run-process":
        xp.run_process(args.process)
    elif args.command == "run-pilot":
        xp.run_pilot(args.pilot_path, process_folder=args.process_folder)
    xp.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
