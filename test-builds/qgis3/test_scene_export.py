import importlib.util
import pathlib
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('scene_export', pathlib.Path(__file__).parent / 'q3d_decimal_degrees' / 'scene_export.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExportTests(unittest.TestCase):
    def test_each_scene_gets_content_addressed_script(self):
        with tempfile.TemporaryDirectory() as directory:
            first = pathlib.Path(directory) / 'one.html'
            second = pathlib.Path(directory) / 'two.html'
            first.write_text('<body><script type="module"></script><td id="qr_coords"></td></body>', encoding='utf-8')
            second.write_text(first.read_text(encoding='utf-8'), encoding='utf-8')
            one = module.add_scene_script(first, 'first')
            two = module.add_scene_script(second, 'second')
            self.assertNotEqual(one, two)
            self.assertEqual((first.parent / one).read_text(encoding='utf-8'), 'first')
            self.assertIn(one, first.read_text(encoding='utf-8'))
            self.assertIn(two, second.read_text(encoding='utf-8'))

    def test_reject_unexpected_template(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'bad.html'
            path.write_text('<body></body>', encoding='utf-8')
            with self.assertRaises(ValueError): module.add_scene_script(path, 'script')
            self.assertEqual(path.read_text(encoding='utf-8'), '<body></body>')


if __name__ == '__main__': unittest.main()
