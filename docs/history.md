# Dispatch desk notes

2026-10-12T09:00:00+00:00, archived ticket vocabulary: a job was called a ticket and the worker proposal used minute-valued retry delays. Neither term defines the current file format.

2026-11-26T14:00:00+00:00, Saskia Pell: the proposal to schedule retries from the operator's restart time was rejected. A late restart must not move an already-known retry deadline into the future. Current `docs/contracts.md` uses UTC-seconds clocks and completion-relative delays. The current contract supersedes the October proposal.

2026-11-30T15:00:00+00:00, Taline Vos: keep whole-file JSON while this remains one offline operator. A future SQLite projection is possible, but it must preserve the public Python functions and JSON command results. No database install or migration tool is needed today.
