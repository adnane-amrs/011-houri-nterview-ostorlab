"""Read-only structural and tenant capacity findings."""
from __future__ import annotations

from dispatch_cli import models


def preflight(ledger: models.Record, config: models.Record, tenant: str) -> list[str]:
    """Report corruption anywhere, but count capacity only for the chosen tenant."""
    errors: list[str] = []
    try:
        models.require_schema(ledger)
    except models.Error as error:
        return [str(error)]
    if isinstance(tenant, str) is False or tenant.strip() == "":
        errors.append("tenant must be a nonblank string")
    for field in ("queue_limit", "retry_delay", "max_attempts"):
        value = config.get(field)
        if models.is_nonnegative_int(value) is False or (field == "max_attempts" and value == 0):
            errors.append(f"config {field} must be a valid integer")
    identities: set[tuple[str, str]] = set()
    active = 0
    for index, job in enumerate(ledger["jobs"]):
        label = f"job[{index}]"
        if isinstance(job, dict) is False:
            errors.append(f"{label} must be an object")
            continue
        identity_valid = True
        for field in ("tenant", "job_id"):
            if isinstance(job.get(field), str) is False or job[field].strip() == "":
                errors.append(f"{label} {field} must be nonblank")
                identity_valid = False
        if identity_valid is True:
            identity = (job["tenant"], job["job_id"])
            if identity in identities:
                errors.append(f"{label} duplicate tenant/job_id")
            identities.add(identity)
        if job.get("state") not in models.STATES:
            errors.append(f"{label} state is invalid")
        if job.get("tenant") == tenant and job.get("state") in ("queued", "running"):
            active += 1
        for field in ("not_before", "attempt_count", "retry_delay", "max_attempts"):
            value = job.get(field)
            if models.is_nonnegative_int(value) is False or (field == "max_attempts" and value == 0):
                errors.append(f"{label} {field} must be a valid integer")
        for field in ("last_finished_at", "lease_until"):
            value = job.get(field)
            if field not in job or (value is not None and models.is_nonnegative_int(value) is False):
                errors.append(f"{label} {field} must be null or a valid clock")
            elif job.get("state") == "running" and value is None:
                errors.append(f"{label} running requires {field}")
    observations: set[tuple[str, str, int]] = set()
    for index, attempt in enumerate(ledger["attempts"]):
        label = f"attempt[{index}]"
        if isinstance(attempt, dict) is False:
            errors.append(f"{label} must be an object")
            continue
        identity_valid = True
        for field in ("tenant", "job_id"):
            if isinstance(attempt.get(field), str) is False or attempt[field].strip() == "":
                errors.append(f"{label} {field} must be nonblank")
                identity_valid = False
        if identity_valid is True and (attempt["tenant"], attempt["job_id"]) not in identities:
            errors.append(f"{label} unknown job reference")
        number = attempt.get("attempt_no")
        if models.is_nonnegative_int(number) is False or number == 0:
            errors.append(f"{label} attempt_no must be positive integer")
        elif identity_valid is True:
            observation = (attempt["tenant"], attempt["job_id"], number)
            if observation in observations:
                errors.append(f"{label} duplicate attempt_no")
            observations.add(observation)
        if attempt.get("outcome") not in ("success", "transient", "permanent"):
            errors.append(f"{label} outcome is invalid")
        if models.is_nonnegative_int(attempt.get("finished_at")) is False:
            errors.append(f"{label} finished_at must be a valid clock")
    limit = config.get("queue_limit")
    if models.is_nonnegative_int(limit) is True and active > limit:
        errors.append(f"tenant {tenant} active load {active} exceeds queue_limit {limit}")
    return errors
