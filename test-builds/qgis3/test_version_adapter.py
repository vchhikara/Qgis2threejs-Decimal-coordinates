import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location(
    'version_adapter', Path(__file__).parent / 'q3d_decimal_degrees' / 'version_adapter.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class VersionAdapterTests(unittest.TestCase):
    def test_known_integration_families(self):
        self.assertEqual(adapter.exporter_module('2.8', 3), 'Qgis2threejs.export')
        self.assertEqual(adapter.exporter_module('2.9', 3), 'Qgis2threejs.core.export.export')
        self.assertEqual(adapter.exporter_module('2.10.2', 3), 'Qgis2threejs.core.export.export')
        self.assertEqual(adapter.exporter_module('3.3', 4), 'Qgis2threejs.core.export.export')
        self.assertEqual(adapter.exporter_module('2.10.2', 4), 'Qgis2threejs.core.export.export')

    def test_reject_unverified_and_wrong_edition(self):
        for version, edition in [('2.7', 3), ('2.10.3', 3), ('3.3', 3),
                                 ('3.3.1', 4), ('2.9', 4), ('3.3-beta', 4),
                                 ('', 3), (None, 3)]:
            with self.subTest(version=version, edition=edition):
                self.assertIsNone(adapter.exporter_module(version, edition))

    def test_cancelled_export_is_not_modified(self):
        self.assertFalse(adapter.export_succeeded(False))
        self.assertTrue(adapter.export_succeeded(True))
        self.assertTrue(adapter.export_succeeded(None))


if __name__ == '__main__':
    unittest.main()
