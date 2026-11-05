# Choices: local cancellation handoff

## What I built

I fixed `queue.cancel_job` (the `cancel` command). It could cancel the wrong tenant's job, used the wrong time and ignored the reason. Now:

- The job is found by tenant + job_id together.
- A missing job and another tenant's job give the same error: `job unavailable`.
- Queued or running jobs become `cancelled` and `lease_until` becomes null. Nothing else changes.
- One audit row is added with the given time and the exact reason.
- Cancelling an already cancelled job changes nothing.
- Done or failed jobs are refused. No file is written.
- The input is never modified.

`storage.py` and `__main__.py` were already correct: safe atomic write, separate output path.

## Checks

- 24 tests pass. I added tests for a running job, time 0, the same job ID in two tenants, failed jobs, and the CLI (success, repeat, conflict, same path).
- Manual runs on `fixtures/ledger.json`: success exits 0, a repeat gives an identical file, and the source hash is unchanged.

## Limits of this handoff

This file only records that someone asked for a cancellation. It does not prove that a worker received the request, stopped the scan or was notified. Check the worker separately. Only one operator should write at a time.

## Not done

No worker communication, retry, upgrade or UI changes. No file locking.

## AI use and a local check

I used Claude to draft the fix and tests. I did not trust it alone: I ran every case myself. Example: cancelling done job `scan-c` printed `job scan-c is done and cannot be cancelled`, exited 2, and `conflict.json` still said `previous proposal`. The old `cancel_requested` flag in the starting code was a v1 leftover; `upgrade.py` turns it into `state = "cancelled"`.
