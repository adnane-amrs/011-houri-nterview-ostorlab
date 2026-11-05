"""Tenant and transition boundaries of the public queue interface."""
import copy
import json
import pathlib
import unittest

from dispatch_cli import models
from dispatch_cli import queue


class QueueTest(unittest.TestCase):
    def setUp(self) -> None:
        path = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "ledger.json"
        self.ledger: models.Record = json.loads(path.read_text(encoding="utf-8"))

    def testSummary_withSharedIdsAndUnorderedObservations_scopesLatestAndOrdersRows(self) -> None:
        self.ledger["attempts"].extend([
            {"tenant": "amber", "job_id": "scan-a", "attempt_no": 3, "outcome": "success", "finished_at": 9},
            {"tenant": "amber", "job_id": "scan-a", "attempt_no": 1, "outcome": "transient", "finished_at": 8},
        ])
        self.ledger["jobs"].reverse()
        original = copy.deepcopy(self.ledger)
        report = queue.build_summary(self.ledger, "amber", 18000)
        self.assertEqual(report["counts"], {"queued": 1, "running": 1, "done": 1, "failed": 0, "cancelled": 0})
        self.assertEqual(report["ready"], 1)
        self.assertEqual([row["job_id"] for row in report["jobs"]], ["scan-a", "scan-b", "scan-c"])
        self.assertEqual(report["jobs"][0]["attempts"], 2)
        self.assertEqual(report["jobs"][0]["latest_outcome"], "success")
        self.assertEqual(queue.build_summary(self.ledger, "amber", 17999)["ready"], 0)
        self.assertEqual(self.ledger, original)

    def testCancel_withRepeatedRequest_preservesInputAndAppendsOnce(self) -> None:
        original = copy.deepcopy(self.ledger)
        result = queue.cancel_job(self.ledger, "amber", "scan-a", "handoff", 18000)
        self.assertEqual(result["jobs"][0]["state"], "cancelled")
        self.assertIsNone(result["jobs"][0]["lease_until"])
        self.assertEqual(result["jobs"][3], original["jobs"][3])
        self.assertEqual(result["attempts"], original["attempts"])
        self.assertEqual(result["audit"][-1], {"tenant": "amber", "job_id": "scan-a", "event": "cancelled", "at": 18000, "reason": "handoff"})
        self.assertEqual(queue.cancel_job(result, "amber", "scan-a", "again", 18001), result)
        self.assertEqual(self.ledger, original)
        result["jobs"][0]["job_id"] = "copy-only"
        self.assertEqual(self.ledger, original)

    def testCancel_withUnavailableCompletedOrBlankReason_rejectsWithoutMutation(self) -> None:
        original = copy.deepcopy(self.ledger)
        for tenant, job_id, reason in (("missing", "scan-a", "handoff"), ("amber", "scan-c", "handoff"), ("amber", "scan-a", "  ")):
            with self.subTest(tenant=tenant, job_id=job_id):
                with self.assertRaises(models.Error):
                    queue.cancel_job(self.ledger, tenant, job_id, reason, 18000)
        self.assertEqual(self.ledger, original)

    def testCancel_withRunningJobAtClockZero_clearsLeaseAndKeepsOtherFields(self) -> None:
        result = queue.cancel_job(self.ledger, "amber", "scan-b", " keep spacing ", 0)
        expected = dict(self.ledger["jobs"][1], state="cancelled", lease_until=None)
        self.assertEqual(result["jobs"][1], expected)
        self.assertNotIn("cancel_requested", result["jobs"][1])
        self.assertEqual(result["audit"], [{"tenant": "amber", "job_id": "scan-b", "event": "cancelled", "at": 0, "reason": " keep spacing "}])
        self.assertEqual(result["desk_note"], self.ledger["desk_note"])

    def testCancel_withSharedIdInOtherTenant_changesOnlySelectedIdentity(self) -> None:
        result = queue.cancel_job(self.ledger, "teal", "scan-a", "handoff", 18000)
        self.assertEqual(result["jobs"][3]["state"], "cancelled")
        self.assertEqual(result["jobs"][0], self.ledger["jobs"][0])
        self.assertEqual(result["audit"][-1]["tenant"], "teal")

    def testCancel_withFailedOrUnknownTargets_reportsConflictOrSameUnavailableError(self) -> None:
        self.ledger["jobs"][2]["state"] = "failed"
        with self.assertRaisesRegex(models.Error, "failed"):
            queue.cancel_job(self.ledger, "amber", "scan-c", "handoff", 18000)
        messages = []
        for tenant, job_id in (("amber", "scan-z"), ("teal", "scan-b")):
            with self.assertRaises(models.Error) as caught:
                queue.cancel_job(self.ledger, tenant, job_id, "handoff", 18000)
            messages.append(str(caught.exception))
        self.assertEqual(messages, ["job unavailable", "job unavailable"])

    def testRecover_atLeaseBoundary_usesCompletionDeadlineAndIsIdempotent(self) -> None:
        original = copy.deepcopy(self.ledger)
        self.assertEqual(queue.recover_jobs(self.ledger, "amber", 17999), original)
        result = queue.recover_jobs(self.ledger, "amber", 18100)
        self.assertEqual(result["jobs"][1]["state"], "queued")
        self.assertEqual(result["jobs"][1]["not_before"], 18000)
        self.assertEqual(result["jobs"][1]["attempt_count"], 1)
        self.assertEqual(result["audit"][-1]["event"], "retry_queued")
        self.assertEqual(queue.recover_jobs(result, "amber", 18100), result)
        self.assertEqual(self.ledger, original)
        self.assertEqual(queue.recover_jobs(self.ledger, "amber", 18000)["jobs"][1]["state"], "queued")

    def testRecover_withExhaustedBudget_marksFailedWithoutMovingDeadline(self) -> None:
        self.ledger["jobs"][1]["attempt_count"] = self.ledger["jobs"][1]["max_attempts"]
        result = queue.recover_jobs(self.ledger, "amber", 18000)
        self.assertEqual(result["jobs"][1]["state"], "failed")
        self.assertEqual(result["jobs"][1]["not_before"], self.ledger["jobs"][1]["not_before"])
        self.assertEqual(result["audit"][-1]["event"], "retry_exhausted")

    def testQueue_withBooleanClock_rejectsInput(self) -> None:
        with self.assertRaises(models.Error):
            queue.build_summary(self.ledger, "amber", True)
