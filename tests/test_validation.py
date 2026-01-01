"""Readiness distinguishes structural integrity from tenant capacity."""
import copy
import json
import pathlib
import unittest

from dispatch_cli import models
from dispatch_cli import validation


class ValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        path = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "ledger.json"
        self.ledger: models.Record = json.loads(path.read_text(encoding="utf-8"))
        self.config = {"queue_limit": 2, "retry_delay": 0, "max_attempts": 1}

    def testPreflight_withExactTenantCapacity_acceptsRunningAndQueued(self) -> None:
        original = copy.deepcopy(self.ledger)
        self.assertEqual(validation.preflight(self.ledger, self.config, "amber"), [])
        self.config["queue_limit"] = 1
        self.assertIn("queue_limit", " ".join(validation.preflight(self.ledger, self.config, "amber")))
        self.assertEqual(validation.preflight(self.ledger, self.config, "teal"), [])
        self.assertEqual(self.ledger, original)

    def testPreflight_withDuplicateAndUnknownReferences_reportsRelevantRecords(self) -> None:
        self.ledger["jobs"].append(copy.deepcopy(self.ledger["jobs"][0]))
        self.ledger["attempts"].append(copy.deepcopy(self.ledger["attempts"][0]))
        self.ledger["attempts"].append({"tenant": "other", "job_id": "absent", "attempt_no": 1, "outcome": "success", "finished_at": 0})
        errors = " ".join(validation.preflight(self.ledger, self.config, "amber"))
        self.assertIn("duplicate tenant/job_id", errors)
        self.assertIn("duplicate attempt_no", errors)
        self.assertIn("unknown job reference", errors)

    def testPreflight_withOtherTenantCorruption_reportsStructuralFields(self) -> None:
        self.ledger["jobs"][3]["retry_delay"] = True
        self.ledger["jobs"][3]["max_attempts"] = 0
        self.ledger["attempts"][0]["attempt_no"] = False
        errors = " ".join(validation.preflight(self.ledger, self.config, "amber"))
        for field in ("retry_delay", "max_attempts", "attempt_no"):
            self.assertIn(field, errors)

    def testPreflight_withInvalidShapeAndConfiguration_returnsFindings(self) -> None:
        self.assertIn("jobs", " ".join(validation.preflight({"schema": 2}, self.config, "amber")))
        for field in self.config:
            config = dict(self.config)
            config[field] = True
            self.assertIn(field, " ".join(validation.preflight(self.ledger, config, "amber")))
        self.ledger["jobs"][1]["lease_until"] = None
        self.assertIn("lease_until", " ".join(validation.preflight(self.ledger, self.config, "amber")))
