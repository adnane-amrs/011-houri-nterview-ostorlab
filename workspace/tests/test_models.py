"""Clock and shape checks used across the operator tools."""
import unittest

from dispatch_cli import models


class ModelsTest(unittest.TestCase):
    def testClock_withZeroAndBooleans_preservesIntegerDistinction(self) -> None:
        self.assertTrue(models.is_nonnegative_int(0))
        self.assertFalse(models.is_nonnegative_int(True))
        self.assertFalse(models.is_nonnegative_int(-1))

    def testSchema_withUnknownVersion_rejectsInput(self) -> None:
        with self.assertRaises(models.Error):
            models.require_schema({'schema': 9, 'jobs': [], 'attempts': [], 'audit': []})
