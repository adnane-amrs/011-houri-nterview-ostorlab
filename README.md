# Make local cancellation reliable

**1 December 2026, 10:30 UTC+00:00.** You are helping Velmoraft’s worker-observation owner, Javed Miro. Operators prepare local cancellation proposals to hand over between shifts. The command exists, but the record cannot yet be trusted in several ordinary cases.

## Your mission

Give Javed a reliable, checkable local cancellation handoff through the documented Python function and CLI. Another operator should be able to identify what changed, why, and what remains unproven about remote work.

At minimum, make the current cancellation contract work, demonstrate its success and conflict behavior with small local examples, and explain the handoff’s limits. Aim for a useful core by minute 35, verification through minute 45, then submission by minute 50. Anything beyond that is up to you; no remote worker or interface is needed.

There is no single right answer. Choose how you organize the transition and supporting evidence; explain your choices in `CHOICES.md`.

## What you have

`workspace/` contains a Python 3.11+ standard-library CLI and small JSON fixtures. Start with `README.md`, `SOURCE_MAP.md` and `docs/cancellation-request.md`. The current `docs/contracts.md` defines identities, state changes, audit contents and output safety. `queue.py` owns the public transition; `__main__.py` and `storage.py` connect it to local files. `hints.md` supports offline checks. Other commands and archived background are optional.

From the exported root, setup: `cd workspace && python3 -B -m dispatch_cli selfcheck` before the timer. From `workspace/`, tests: `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`. Example: `python3 -B -m dispatch_cli cancel fixtures/ledger.json --tenant amber --job scan-a --reason 'shift handoff' --now 18000 --out /tmp/velmoraft-proposal.json`. Setup checks the environment; task tests may fail initially.

Everything is fictional; local files are the only source of truth. No research, downloads, packages, accounts, scanner, service or internet connection is required.

## Rules

- You have **50 minutes** of active work after setup succeeds. The session is recorded; pause for technical interruptions.
- Use any editor and local tools. We encourage AI when available; local hints and Python provide an equally valid offline route. Verification matters, not subscriptions or connection speed.
- The engineer helps with setup, audio and time only. Make reasonable assumptions and record them in `CHOICES.md`.
- Do not contact real people or systems, publish anything or use real credentials. Any `DEMO` values are nonfunctional.
- Keep source data unchanged and write proposals separately. A local cancellation record does not prove a worker received it or stopped remote work.

## What to send at minute 50

Send your changed workspace and `CHOICES.md` (at most 300 words): what you built and why, deferred work, checks and handoff limits, plus an AI output corrected/rejected or a local verification example if AI was unavailable. Unfinished work is fine; explain next steps.

## How it is assessed

Result 35, accuracy 25, judgment 20, process 20: usefulness to Javed, source correctness, sensible scope and verification visible in the recording. Every approach can reach full marks. Typing speed, tool brand, machine speed, connection quality, polish and volume are not scored.
