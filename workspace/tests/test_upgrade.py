"""Migration retains falsy extensions and never advances dispatch timing."""
import copy
import json
import pathlib
import unittest

from dispatch_cli import models
from dispatch_cli import upgrade


class UpgradeTest(unittest.TestCase):
    def setUp(self) -> None:
        path = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "legacy.json"
        self.ledger: models.Record = json.loads(path.read_text(encoding="utf-8"))

    def testUpgrade_withFractionalSecondAndFalsyExtensions_preservesMeaningAndInput(self) -> None:
        original = copy.deepcopy(self.ledger)
        result = upgrade.upgrade_ledger(self.ledger)
        job = result["jobs"][0]
        self.assertEqual(result["schema"], 2)
        self.assertEqual(job["not_before"], 18001)
        self.assertEqual(job["retry_delay"], 0)
        self.assertIsNone(job["last_finished_at"])
        self.assertEqual(job["state"], "queued")
        self.assertNotIn("cancel_requested", job)
        self.assertNotIn("run_after_ms", job)
        for key, value in original["jobs"][0].items():
            if key not in ("run_after_ms", "last_finished_ms", "lease_until_ms", "retry_delay_ms", "cancel_requested"):
                self.assertEqual(job[key], value)
        self.assertEqual(self.ledger, original)
        self.assertEqual(upgrade.upgrade_ledger(result), result)
        self.assertIsNot(upgrade.upgrade_ledger(result)["jobs"], result["jobs"])

    def testUpgrade_withCancellationFlag_preservesTerminalState(self) -> None:
        for state, expected in (("queued", "cancelled"), ("running", "cancelled"), ("done", "done"), ("failed", "failed")):
            with self.subTest(state=state):
                self.ledger["jobs"][0].update({"state": state, "cancel_requested": True, "last_finished_ms": 1001, "lease_until_ms": 2001})
                result = upgrade.upgrade_ledger(self.ledger)
                self.assertEqual(result["jobs"][0]["state"], expected)
                self.assertEqual(result["jobs"][0]["last_finished_at"], 2)
                self.assertEqual(result["jobs"][0]["lease_until"], None if expected == "cancelled" else 3)

    def testUpgrade_withAttemptAndAuditClocks_roundsUpAndPreservesExtensions(self) -> None:
        job = self.ledger["jobs"][0]
        self.ledger["attempts"] = [{"tenant": job["tenant"], "job_id": job["job_id"], "attempt_no": 1, "outcome": "transient", "finished_ms": 1001, "note": False}]
        self.ledger["audit"] = [{"at_ms": 1, "event": "created", "extra": {"empty": ""}}]
        result = upgrade.upgrade_ledger(self.ledger)
        self.assertEqual(result["attempts"][0]["finished_at"], 2)
        self.assertIs(result["attempts"][0]["note"], False)
        self.assertEqual(result["audit"][0], {"at": 1, "event": "created", "extra": {"empty": ""}})

    def testUpgrade_withInvalidClockOrStructure_rejectsWithoutMutation(self) -> None:
        for invalid in (True, -1, 1.5, "1000"):
            with self.subTest(invalid=invalid):
                self.ledger["jobs"][0]["run_after_ms"] = invalid
                original = copy.deepcopy(self.ledger)
                with self.assertRaises(models.Error):
                    upgrade.upgrade_ledger(self.ledger)
                self.assertEqual(self.ledger, original)
        self.ledger["schema"] = 7
        with self.assertRaises(models.Error):
            upgrade.upgrade_ledger(self.ledger)

    def testUpgrade_withInvalidRunningShape_rejectsBeforeCancellation(self) -> None:
        self.ledger["jobs"][0].update({"state": "running", "cancel_requested": True, "lease_until_ms": None})
        with self.assertRaises(models.Error):
            upgrade.upgrade_ledger(self.ledger)
