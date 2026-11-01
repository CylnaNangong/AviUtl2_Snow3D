"""Dependency-free package regression checks: python -m unittest discover -s tests -v."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('snow_package', ROOT / 'packaging/build_au2pkg.py')
pkg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pkg)


class PackageTests(unittest.TestCase):
    def test_versions_match(self):
        for name in ('packaging/package.ini', 'packaging/package.txt',
                     f'Script/{pkg.SCRIPT_NAME}', 'README.md',
                     'docs/README_en.md', 'docs/README_ja.md'):
            with self.subTest(file=name):
                self.assertIn(pkg.VERSION, (ROOT / name).read_text(encoding='utf-8'))
        self.assertIn(f'--information:雪（3D）{pkg.VERSION}',
                      (ROOT / 'Script' / pkg.SCRIPT_NAME).read_text(encoding='utf-8'))

    def test_package_contents_and_reproducibility(self):
        expected = {
            'package.ini': ROOT / 'packaging/package.ini',
            'package.txt': ROOT / 'packaging/package.txt',
            f'Script/{pkg.SCRIPT_NAME}': ROOT / 'Script' / pkg.SCRIPT_NAME,
        }
        languages = list((ROOT / 'Language').glob(f'*{pkg.LANG_SUFFIX}'))
        self.assertEqual(len(languages), 4)
        expected.update({f'Language/{p.name}': p for p in languages})
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / 'a.zip', Path(tmp) / 'b.zip'
            pkg.build_package(ROOT, first)
            pkg.build_package(ROOT, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(set(archive.namelist()), set(expected))
                self.assertEqual(len(archive.namelist()), 7)
                for name, source in expected.items():
                    with self.subTest(entry=name):
                        data = archive.read(name)
                        data.decode('utf-8')
                        self.assertEqual(data, pkg.to_crlf(source.read_bytes()))
                        self.assertNotIn(b'\n', data.replace(b'\r\n', b''))

    def test_line_ending_normalization(self):
        self.assertEqual(pkg.to_crlf(b'a\nb\r\nc\n'), b'a\r\nb\r\nc\r\n')


if __name__ == '__main__':
    unittest.main()
