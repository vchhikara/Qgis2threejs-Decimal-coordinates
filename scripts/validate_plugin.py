"""Check a plugin ZIP against the plugins.qgis.org package rules."""
import configparser, sys, zipfile

REQUIRED_KEYS = ['name', 'qgisMinimumVersion', 'description', 'about', 'version',
                 'author', 'email', 'repository', 'tracker', 'homepage']
MANDATORY = ['__init__.py', 'metadata.txt', 'LICENSE', 'icon.png']

def main(path):
    errors = []
    z = zipfile.ZipFile(path)
    names = z.namelist()
    roots = {n.split('/')[0] for n in names}
    if len(roots) != 1:
        errors.append('ZIP must have one top-level folder: %s' % roots)
    root = next(iter(roots))
    for m in MANDATORY:
        if '%s/%s' % (root, m) not in names:
            errors.append('missing ' + m)
    for n in names:
        if '..' in n or '__pycache__' in n or n.endswith('.pyc') or '.git' in n:
            errors.append('forbidden path ' + n)
    import os
    if os.path.getsize(path) > 25 * 1024 * 1024:
        errors.append('ZIP larger than 25 MB')
    cp = configparser.ConfigParser(strict=False)
    cp.read_string(z.read('%s/metadata.txt' % root).decode())
    for k in REQUIRED_KEYS:
        if not cp['general'].get(k):
            errors.append('metadata key missing: ' + k)
    if 'def classFactory' not in z.read('%s/__init__.py' % root).decode():
        errors.append('classFactory missing')
    print('\n'.join(errors) or 'OK: %s (%d files, %d bytes)' % (root, len(names), os.path.getsize(path)))
    sys.exit(1 if errors else 0)

main(sys.argv[1])
