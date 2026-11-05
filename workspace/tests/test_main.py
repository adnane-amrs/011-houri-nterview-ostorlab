"""CLI cancellation writes a separate proposal and leaves files alone on failure."""
import contextlib
import io
import json
import pathlib
import shutil
import tempfile
import unittest

from dispatch_cli import __main__ as cli

FIXTURE = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "ledger.json"


class CancelCommandTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source = pathlib.Path(self.directory.name) / "ledger.json"
        shutil.copyfile(FIXTURE, self.source)
        self.out = pathlib.Path(self.directory.name) / "proposal.json"

    def cancel(self, ledger: pathlib.Path, job_id: str, out: pathlib.Path) -> int:
        argv = ["cancel", str(ledger), "--tenant", "amber", "--job", job_id,
                "--reason", "shift handoff", "--now", "18000", "--out", str(out)]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return cli.main(argv)

    def testCancel_withQueuedJob_writesProposalAndRepeatAddsNothing(self) -> None:
        before = self.source.read_bytes()
        self.assertEqual(self.cancel(self.source, "scan-a", self.out), 0)
        self.assertEqual(self.source.read_bytes(), before)
        proposal = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(proposal["jobs"][0]["state"], "cancelled")
        self.assertEqual(len(proposal["audit"]), 1)
        second = pathlib.Path(self.directory.name) / "second.json"
        self.assertEqual(self.cancel(self.out, "scan-a", second), 0)
        self.assertEqual(json.loads(second.read_text(encoding="utf-8")), proposal)

    def testCancel_withDoneJobOrSamePath_exitsTwoAndKeepsBytes(self) -> None:
        before = self.source.read_bytes()
        self.out.write_bytes(b"previous proposal")
        self.assertEqual(self.cancel(self.source, "scan-c", self.out), 2)
        self.assertEqual(self.out.read_bytes(), b"previous proposal")
        self.assertEqual(self.cancel(self.source, "scan-a", self.source), 2)
        self.assertEqual(self.source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
