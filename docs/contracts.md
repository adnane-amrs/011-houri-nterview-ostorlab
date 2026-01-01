# Current dispatch contracts

Owner: Saskia Pell. Effective 2026-12-01T09:00:00+00:00. This page supersedes archived proposals. Everything is a local simulation. No command contacts a worker, dispatches a scan or authenticates a tenant.

## Files and clocks

A schema-2 ledger is an object with integer `schema: 2`, `jobs`, `attempts` and `audit` lists. Extra fields are preserved by write operations. Identity is `(tenant, job_id)`; IDs can repeat across tenants. Jobs have nonempty string `tenant` and `job_id`; `state` is queued, running, done, failed or cancelled. Numeric fields `not_before`, `attempt_count`, `retry_delay` and `max_attempts` are integer seconds/counts, not booleans. Counts/delays are nonnegative; max_attempts is at least one. Nullable `last_finished_at` and `lease_until` are integer seconds when present. Running jobs have a lease and last completion time. A queued job is ready exactly when `not_before <= now`. Other states are never ready.

Example clock `18000` is a small synthetic UTC-seconds value, not the wall clock. Zero is meaningful and `null` is not zero. All operations taking `now` require a nonnegative integer. Attempt records contain `tenant`, `job_id`, positive `attempt_no`, `outcome` (success/transient/permanent), and nonnegative `finished_at`. Attempts refer to existing composite job identities. An observation number can appear only once per composite job. Physical file order does not imply observation order.

## Summary: read-only

Public function: `queue.build_summary(ledger, tenant, now) -> dict`. Public command: `summary LEDGER --tenant TENANT --now SECONDS`.

Return `tenant`, `now`, `counts` (every state key including zeros), `ready` (number), and `jobs`. Each job row has `job_id`, `state`, boolean `ready`, integer `attempts` (number of saved attempt observations), and `latest_outcome` (outcome with greatest numeric attempt_no, or null). Sort job rows by job_id ascending. Counts, rows, attempt observations and readiness are tenant-scoped. Never change the ledger, rows or lists. Unknown extension fields need not be displayed.

The supported small growth check counts input job and attempt entries examined, including repeat passes and indexed reads. It does not time a machine. For J jobs and A observations, a bounded pass should inspect no more than `4*(J+A)+20` entries, and doubling both inputs should have roughly linear growth. Indexing, grouped joins or a local SQLite projection are acceptable if the public Python/CLI interface and read-only behavior remain intact. A counter reported by the implementation alone is not evidence: a counted input sequence can witness entry reads independently.

## Operator preflight: read-only

Public function: `validation.preflight(ledger, config, tenant) -> list[str]`. Empty errors means locally ready. CLI emits `{ok: bool, errors: [...]}` and exits 0 for ready, 1 for findings, 2 for invalid JSON or IO failure. No repairs, output ledger or other writes.

Check schema2 shape; required job fields/types/states; composite duplicate jobs; attempt shape, duplicate composite observation numbers and unknown references. Config requires strict integers: nonnegative queue_limit and retry_delay, positive max_attempts. The selected tenant's active load is queued plus running; reject only when this exceeds queue_limit, so an exact limit is valid. Other tenants' active load is excluded; structural corruption anywhere still produces findings. A local pass proves file consistency and capacity only, not remote worker health, authentication or delivery. Human-readable finding wording is open, but must identify the relevant field or record.

## Cancellation handoff

Public function: `queue.cancel_job(ledger, tenant, job_id, reason, now) -> new ledger`. CLI adds `--job`, `--reason`, `--out`. Reason must be a nonblank string; now a valid clock. Find the job within tenant scope. Missing and other-tenant records produce the same unavailable error. Queued or running becomes cancelled, lease_until becomes null, all other job fields remain. Append exactly one audit row `{tenant, job_id, event: "cancelled", at: now, reason}`. Already cancelled returns an equal copy, appending nothing. Done/failed conflicts and leaves everything untouched. No other tenant, attempt observation or extension field changes. This records a local request; it does not prove any remote work stopped.

## Retry recovery

Public function: `queue.recover_jobs(ledger, tenant, now) -> new ledger`. CLI `recover` writes a separate proposal. Only selected-tenant running jobs whose `lease_until <= now` qualify. Completed attempt_count includes the saved failed attempt; retry is available exactly when attempt_count < max_attempts. A retry returns to queued, clears lease_until and sets not_before = last_finished_at + retry_delay, even if that deadline is in the past. Do not schedule from operator restart time. At exhausted budget, state becomes failed and lease_until clears, while not_before stays unchanged. Other states/tenants stay unchanged. Every transitioned job appends one audit row `{tenant, job_id, event: "retry_queued" or "retry_exhausted", at: now}`. Rerunning the same proposal produces no new transition/audit. Attempt counts and observations do not change. No scan is actually retried.

## Legacy schema upgrade

Public function: `upgrade.upgrade_ledger(ledger) -> new ledger`. CLI `upgrade LEDGER --out OTHER`. V1 has the same root lists, identities and state vocabulary. Job legacy keys are run_after_ms, last_finished_ms (nullable), lease_until_ms (nullable), retry_delay_ms; these replace v2 not_before, last_finished_at, lease_until, retry_delay. Attempt finished_ms replaces finished_at. Audit at_ms replaces at. Nonnegative integer milliseconds convert with ceiling division `(ms + 999) // 1000`, so 18000001 becomes 18001, never an early dispatch. Null remains null in nullable fields, zero remains zero, booleans are invalid clocks. Remove only the consumed legacy fields. Preserve all unknown nested values, including empty strings, zero and false.

Each v1 job also has boolean cancel_requested. True changes queued/running to cancelled and clears lease_until; it does not turn done/failed into cancelled. False preserves state. Consume the flag. Do not invent audit rows or worker acknowledgements. Return root schema2. Reapplying to an already valid schema2 yields an equal deep copy. Reject unsupported schemas, invalid legacy clocks and invalid required structures before any output file is replaced.

## Local storage and exit behavior

All JSON commands print a JSON result to stdout; errors go to stderr and exit2. Argument errors also exit2. Successful summary/cancel/recover/upgrade exit0. All writing commands require an output path distinct from the input. Validate/compute first, then atomically replace the output with complete UTF-8 JSON. On error, source bytes and pre-existing output bytes remain unchanged. Input functions are pure: even successful transformations never mutate their argument. Single-operator whole-file semantics do not promise concurrent writer safety.
