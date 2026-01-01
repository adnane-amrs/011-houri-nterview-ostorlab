"""Real temporary files exercise the local handoff storage boundary."""
import pathlib
import tempfile
import unittest

from dispatch_cli import storage


class StorageTest(unittest.TestCase):
    def testStorage_withUnicodeAndFalsyValues_roundTripsExactly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / 'ledger.json'
            data = {'label': 'café', 'zero': 0, 'reviewed': False}
            storage.write_object(target, data)
            self.assertEqual(storage.read_object(target), data)
            self.assertEqual([item.name for item in target.parent.iterdir()], ['ledger.json'])

    def testStorage_withNonserializableValue_preservesOldOutput(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / 'ledger.json'
            target.write_text('old output')
            with self.assertRaises(TypeError):
                storage.write_object(target, {'invalid': object()})
            self.assertEqual(target.read_text(), 'old output')
