"""Build a reproducible plugin ZIP from an allowlist of runtime files."""
import argparse, os, zipfile

PLUGIN_FOLDER = 'Qgis2threejs_Decimal_Coordinates'
INCLUDE = ['__init__.py', 'plugin.py', 'export_support.py', 'decimal_degrees.js',
           'metadata.txt', 'icon.png', 'LICENSE', 'README.md']

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', default='.')
    ap.add_argument('--output', default='dist/%s.zip' % PLUGIN_FOLDER)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    with zipfile.ZipFile(a.output, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted(INCLUDE):
            info = zipfile.ZipInfo('%s/%s' % (PLUGIN_FOLDER, name), (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(os.path.join(a.source, name), 'rb') as f:
                z.writestr(info, f.read())
    print('wrote', a.output)

main()
