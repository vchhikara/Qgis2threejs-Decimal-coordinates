"""Add the optional viewer enhancements to a completed HTML export."""
import hashlib
import os
import re
import tempfile


def add_scene_script(html_path, javascript):
    html_path = os.path.abspath(html_path)
    with open(html_path, encoding='utf-8') as file:
        html = file.read()
    if not re.search(r'id=["\']qr_coords["\']', html) or not re.search(r'<script\b', html, re.I):
        raise ValueError('The export does not contain the expected viewer coordinate element')
    if len(re.findall(r'</body\s*>', html, re.I)) != 1:
        raise ValueError('The export must contain exactly one closing body tag')
    contents = javascript.encode('utf-8')
    name = 'q3d_decimal_coordinates_' + hashlib.sha256(contents).hexdigest()[:16] + '.js'
    tag = '<script src="./' + name + '"></script>'
    if tag in html:
        raise ValueError('The export already includes this viewer script')
    path = os.path.join(os.path.dirname(html_path), name)
    if os.path.exists(path):
        with open(path, 'rb') as file:
            if file.read() != contents:
                raise ValueError('A conflicting viewer script already exists')
    else:
        with open(path, 'xb') as file:
            file.write(contents)
    result = re.sub(r'</body\s*>', lambda match: tag + '\n' + match.group(0), html, count=1, flags=re.I)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='',
                                         dir=os.path.dirname(html_path), delete=False) as file:
            temporary = file.name
            file.write(result)
        os.replace(temporary, html_path)
    finally:
        if temporary and os.path.exists(temporary): os.unlink(temporary)
    return name
