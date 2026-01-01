# Velmoraft dispatch desk

A small local ledger used by Orien Vale to prepare scan-dispatch handoffs. These are fictional jobs and saved worker observations; no command connects to a scanner. Python 3.11+ and its standard library are sufficient. No installation, server, account or network is used.

```
python3 -B -m dispatch_cli selfcheck
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
python3 -B -m dispatch_cli summary fixtures/ledger.json --tenant amber --now 18000
python3 -B -m dispatch_cli preflight fixtures/ledger.json --config fixtures/config.json --tenant amber
python3 -B -m dispatch_cli cancel fixtures/ledger.json --tenant amber --job scan-a --reason 'operator request' --now 18000 --out /tmp/velmoraft-cancel.json
python3 -B -m dispatch_cli recover fixtures/ledger.json --tenant amber --now 18000 --out /tmp/velmoraft-recovery.json
python3 -B -m dispatch_cli upgrade fixtures/legacy.json --out /tmp/velmoraft-v2.json
```

Start with [SOURCE_MAP.md](SOURCE_MAP.md), then the relevant section of [docs/contracts.md](docs/contracts.md). [hints.md](hints.md) has offline Python commands and terms. [docs/history.md](docs/history.md) preserves superseded proposals; current contracts take precedence.

Whole-file replacement assumes one local operator. The tenant flag filters fixture records; it is not authentication. Cancellation records a local handoff and does not prove that a remote scan stopped. Output paths must differ from input paths, and failed validation leaves existing output untouched.
