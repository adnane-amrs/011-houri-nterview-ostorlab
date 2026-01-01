"""Exit-after-command CLI for a fictional local dispatch ledger."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from dispatch_cli import models
from dispatch_cli import queue
from dispatch_cli import storage
from dispatch_cli import upgrade
from dispatch_cli import validation


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    commands = command.add_subparsers(dest="command", required=True)
    commands.add_parser("selfcheck", help="check interpreter and supplied local fixtures")
    summary = commands.add_parser("summary", help="read-only tenant queue view")
    summary.add_argument("ledger")
    summary.add_argument("--tenant", required=True)
    summary.add_argument("--now", type=int, required=True)
    preflight = commands.add_parser("preflight", help="read-only operator readiness")
    preflight.add_argument("ledger")
    preflight.add_argument("--config", required=True)
    preflight.add_argument("--tenant", required=True)
    for name in ("cancel", "recover"):
        operation = commands.add_parser(name, help="write a new local ledger proposal")
        operation.add_argument("ledger")
        operation.add_argument("--tenant", required=True)
        operation.add_argument("--now", type=int, required=True)
        operation.add_argument("--out", required=True)
        if name == "cancel":
            operation.add_argument("--job", required=True)
            operation.add_argument("--reason", required=True)
    migration = commands.add_parser("upgrade", help="schema1 milliseconds to schema2 seconds")
    migration.add_argument("ledger")
    migration.add_argument("--out", required=True)
    return command


def run(arguments: argparse.Namespace) -> int:
    if arguments.command == "selfcheck":
        fixture_dir = pathlib.Path(__file__).resolve().parent.parent / "fixtures"
        ledger = storage.read_object(fixture_dir / "ledger.json")
        config = storage.read_object(fixture_dir / "config.json")
        errors = validation.preflight(ledger, config, "amber")
        if len(errors) > 0:
            raise models.Error("; ".join(errors))
        print(json.dumps({"ok": True, "mode": "local-only"}, sort_keys=True))
        return 0
    ledger = storage.read_object(arguments.ledger)
    if arguments.command == "summary":
        report = queue.build_summary(ledger, arguments.tenant, arguments.now)
    elif arguments.command == "preflight":
        config = storage.read_object(arguments.config)
        errors = validation.preflight(ledger, config, arguments.tenant)
        print(json.dumps({"ok": len(errors) == 0, "errors": errors}, sort_keys=True))
        return 0 if len(errors) == 0 else 1
    elif arguments.command == "upgrade":
        report = upgrade.upgrade_ledger(ledger)
    elif arguments.command == "cancel":
        report = queue.cancel_job(ledger, arguments.tenant, arguments.job, arguments.reason, arguments.now)
    else:
        report = queue.recover_jobs(ledger, arguments.tenant, arguments.now)
    if arguments.command in ("cancel", "recover", "upgrade"):
        if pathlib.Path(arguments.out).resolve() == pathlib.Path(arguments.ledger).resolve():
            raise models.Error("--out must differ from the input ledger")
        storage.write_object(arguments.out, report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        return run(arguments)
    except (models.Error, OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        print(f"dispatch: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
