# Javed’s cancellation handoff request

2026-12-01T10:30:00+00:00. Javed Miro, worker observation owner.

The desk needs a local cancellation proposal another operator can trust. Keep the existing cancellation command and public function, and show a small reproducible example of the record handed over. A useful handoff distinguishes a locally recorded request from any remote worker action. Nothing in this workspace talks to a worker.

Current rules are docs/contracts.md, Cancellation handoff. Resolve identity using tenant plus job_id. An unavailable target and an ID only present in another tenant receive the same unavailable error. Queued/running targets become cancelled and clear lease_until. Preserve all other fields, extension data, other tenants and saved observations. Append exactly one audit entry using the selected tenant/job, event cancelled, supplied now and supplied reason verbatim. Zero is a valid now; reason must be a nonblank string.

Done or failed targets conflict and must leave source and existing output bytes unchanged. Already cancelled is an equal copied ledger: no replacement reason/time, new flag or second audit entry. The public function must not mutate its input, even on success. Output must use a distinct path and a complete atomic JSON replacement after validation; validation errors must not replace an existing output.

The proposal is local-only. Do not label a remote scan stopped, a worker notified or a message delivered. A short operator-facing explanation can live in CHOICES.md; no extra output field or exact wording is required. No retry, migration, remote communication or UI work is requested.
