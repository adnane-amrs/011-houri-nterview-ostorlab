# Source map

| Need | Open |
| --- | --- |
| Command arguments, output writes, exit codes | `dispatch_cli/__main__.py` |
| Queue grouping, cancellation and retry clocks | `dispatch_cli/queue.py` |
| Operator readiness/config checks | `dispatch_cli/validation.py` |
| Legacy millisecond conversion | `dispatch_cli/upgrade.py` |
| JSON reading and atomic local replacement | `dispatch_cli/storage.py` |
| States and strict integer checks | `dispatch_cli/models.py` |
| Current rules and exact examples | `docs/contracts.md` |
| Small realistic input | `fixtures/ledger.json`, `fixtures/legacy.json`, `fixtures/config.json` |
| Existing checks | `tests/test_*.py` |

The synthetic clock uses seconds: 18000 means the same instant throughout all examples. It does not denote the current wall-clock time. Composite identity means `(tenant, job_id)`, so two tenants can each use `scan-a`.

## Cancellation handoff work

- `docs/cancellation-request.md`: Javed’s current handoff and evidence boundaries.
- `dispatch_cli/queue.py`: public pure `cancel_job` transition.
- `dispatch_cli/__main__.py`: cancellation CLI and separate output path.
- `dispatch_cli/storage.py`: complete atomic local output.
- `docs/contracts.md`: authoritative cancellation and error behavior.
