"""Safely add the companion to a completed Qgis2threejs 2.10.2 export."""
import os
import re
import tempfile

SCRIPT_NAME = 'q3d_decimal_degrees_companion.js'
TAG = '<script src="./' + SCRIPT_NAME + '"></script>'


def prepare_export(html_path, javascript):
    html_path = os.path.abspath(html_path)
    with open(html_path, 'r', encoding='utf-8') as file:
        html = file.read()
    if not re.search(r'id=["\']qr_coords["\']', html) or not re.search(r'<script[^>]+src=["\'][^"\']*Qgis2threejs\.js["\']', html, re.I):
        raise ValueError('Export template does not contain the expected Qgis2threejs coordinate display and script')
    if len(re.findall(r'</body\s*>', html, re.I)) != 1:
        raise ValueError('Export template must contain exactly one closing body tag')
    if TAG in html:
        raise ValueError('Export already references the companion script')
    script_path = os.path.join(os.path.dirname(html_path), SCRIPT_NAME)
    encoded = javascript.encode('utf-8')
    if os.path.exists(script_path):
        with open(script_path, 'rb') as file:
            if file.read() != encoded:
                raise ValueError('A different file already exists at ' + script_path)
    else:
        with open(script_path, 'xb') as file:
            file.write(encoded)
    result = re.sub(r'</body\s*>', lambda m: TAG + '\n' + m.group(0), html, count=1, flags=re.I)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='', dir=os.path.dirname(html_path), delete=False) as file:
            temp_path = file.name
            file.write(result)
        os.replace(temp_path, html_path)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
