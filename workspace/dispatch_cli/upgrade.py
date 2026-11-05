"""Preserve legacy meaning while replacing millisecond fields."""
from __future__ import annotations

import copy

from dispatch_cli import models
from dispatch_cli import validation


def _seconds(value: object, field: str, nullable: bool = False) -> int | None:
    if nullable is True and value is None:
        return None
    if models.is_nonnegative_int(value) is False:
        raise models.Error(f"{field} must be a nonnegative integer clock")
    assert isinstance(value, int)
    return (value + 999) // 1000


def _validate(ledger: models.Record) -> None:
    config = {"queue_limit": len(ledger["jobs"]), "retry_delay": 0, "max_attempts": 1}
    errors = validation.preflight(ledger, config, "upgrade-validation")
    if len(errors) > 0:
        raise models.Error("; ".join(errors))


def upgrade_ledger(ledger: models.Record) -> models.Record:
    """Return a valid schema2 deep copy, consuming only specified legacy keys."""
    if type(ledger.get("schema")) is int and ledger["schema"] == 2:
        models.require_schema(ledger)
        _validate(ledger)
        return copy.deepcopy(ledger)
    models.require_schema(ledger, 1)
    result = copy.deepcopy(ledger)
    cancellations: list[models.Record] = []
    for job in result["jobs"]:
        if isinstance(job, dict) is False:
            raise models.Error("legacy job must be an object")
        for old, new, nullable in (("run_after_ms", "not_before", False),
                                   ("last_finished_ms", "last_finished_at", True),
                                   ("lease_until_ms", "lease_until", True),
                                   ("retry_delay_ms", "retry_delay", False)):
            if old not in job:
                raise models.Error(f"missing {old}")
            job[new] = _seconds(job.pop(old), old, nullable)
        if type(job.get("cancel_requested")) is not bool:
            raise models.Error("cancel_requested must be boolean")
        requested = job.pop("cancel_requested")
        if requested is True and job.get("state") in ("queued", "running"):
            cancellations.append(job)
    for attempt in result["attempts"]:
        if isinstance(attempt, dict) is False or "finished_ms" not in attempt:
            raise models.Error("legacy attempt requires finished_ms")
        attempt["finished_at"] = _seconds(attempt.pop("finished_ms"), "finished_ms")
    for audit in result["audit"]:
        if isinstance(audit, dict) is False or "at_ms" not in audit:
            raise models.Error("legacy audit requires at_ms")
        audit["at"] = _seconds(audit.pop("at_ms"), "at_ms")
    result["schema"] = 2
    _validate(result)
    for job in cancellations:
        job["state"] = "cancelled"
        job["lease_until"] = None
    return result
