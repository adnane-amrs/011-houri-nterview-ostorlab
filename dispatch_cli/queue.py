"""Pure tenant-scoped queue views and local transition proposals."""
from __future__ import annotations

import copy

from dispatch_cli import models
from dispatch_cli import validation


def _check(ledger: models.Record, tenant: str, now: int) -> None:
    models.require_schema(ledger)
    if models.is_nonnegative_int(now) is False:
        raise models.Error("now must be a nonnegative integer")
    config = {"queue_limit": len(ledger["jobs"]), "retry_delay": 0, "max_attempts": 1}
    errors = validation.preflight(ledger, config, tenant)
    if len(errors) > 0:
        raise models.Error("; ".join(errors))


def build_summary(ledger: models.Record, tenant: str, now: int) -> models.Record:
    """Join saved observations by composite identity in bounded input passes."""
    _check(ledger, tenant, now)
    observations: dict[tuple[str, str], list[models.Record]] = {}
    for attempt in ledger["attempts"]:
        if attempt["tenant"] == tenant:
            key = (attempt["tenant"], attempt["job_id"])
            observations.setdefault(key, []).append(attempt)
    counts = dict.fromkeys(models.STATES, 0)
    rows: list[models.Record] = []
    for job in ledger["jobs"]:
        if job["tenant"] != tenant:
            continue
        attempts = observations.get((tenant, job["job_id"]), [])
        latest = max(attempts, key=lambda item: item["attempt_no"], default=None)
        ready = job["state"] == "queued" and job["not_before"] <= now
        counts[job["state"]] += 1
        rows.append({"job_id": job["job_id"], "state": job["state"], "ready": ready,
                     "attempts": len(attempts), "latest_outcome": None if latest is None else latest["outcome"]})
    rows.sort(key=lambda row: row["job_id"])
    return {"tenant": tenant, "now": now, "counts": counts,
            "ready": sum(row["ready"] for row in rows), "jobs": rows}


def cancel_job(ledger: models.Record, tenant: str, job_id: str, reason: str, now: int) -> models.Record:
    """Prepare an operator cancellation handoff."""
    _check(ledger, tenant, now)
    if isinstance(reason, str) is False or reason.strip() == "":
        raise models.Error("reason must be a nonblank string")
    result = copy.deepcopy(ledger)
    for job in result["jobs"]:
        if job["job_id"] == job_id:
            job["cancel_requested"] = True
            job["lease_until"] = None
            result["audit"].append({"tenant": tenant, "job_id": job_id,
                                    "event": "cancelled", "at": now + 1, "reason": "operator request"})
            return result
    raise models.Error("job unavailable")


def recover_jobs(ledger: models.Record, tenant: str, now: int) -> models.Record:
    """Propose completion-relative retries once leases reach their boundary."""
    _check(ledger, tenant, now)
    result = copy.deepcopy(ledger)
    for job in result["jobs"]:
        if job["tenant"] != tenant or job["state"] != "running" or job["lease_until"] > now:
            continue
        job["lease_until"] = None
        if job["attempt_count"] < job["max_attempts"]:
            job["state"] = "queued"
            job["not_before"] = job["last_finished_at"] + job["retry_delay"]
            event = "retry_queued"
        else:
            job["state"] = "failed"
            event = "retry_exhausted"
        result["audit"].append({"tenant": tenant, "job_id": job["job_id"], "event": event, "at": now})
    return result
