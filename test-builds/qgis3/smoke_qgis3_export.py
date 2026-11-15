"""Check the staged export hook against a real Qgis2threejs exporter."""
import os
import functools
import http.server
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path.home() / 'AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get('Q3D_UPSTREAM_ROOT'):
    sys.path.insert(0, os.environ['Q3D_UPSTREAM_ROOT'])
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QSize
from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsMapSettings, QgsRectangle

with tempfile.TemporaryDirectory(dir=str(Path(__file__).resolve().parent)) as directory:
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, directory)
    QCoreApplication.setOrganizationName('DecimalCoordinatesExportTest')
    QCoreApplication.setApplicationName('DecimalCoordinatesExportTest')
    app = QgsApplication([], False, directory)
    app.initQgis()
    from Qgis2threejs.conf import PLUGIN_VERSION
    if PLUGIN_VERSION.startswith('3.'):
        from Qgis2threejs.utils.logging import configureLoggers
        configureLoggers()
    if PLUGIN_VERSION == '2.8':
        from Qgis2threejs.exportsettings import ExportSettings
        from Qgis2threejs.export import ThreeJSExporter
    else:
        from Qgis2threejs.core.exportsettings import ExportSettings
        from Qgis2threejs.core.export.export import ThreeJSExporter
    from q3d_decimal_degrees.plugin import DecimalDegreesPlugin
    from q3d_decimal_degrees.presentation_settings import KEY
    QSettings().setValue(KEY + 'heading', 'Export heading')
    QSettings().setValue(KEY + 'arrow_design', 'NorthArrow_02.svg')
    class Action:
        def isChecked(self): return True
    companion = DecimalDegreesPlugin(None)
    companion.action = Action()
    companion.install_export_hook(ThreeJSExporter)
    settings = ExportSettings()
    map_settings = QgsMapSettings()
    map_settings.setOutputSize(QSize(800, 600))
    map_settings.setDestinationCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
    map_settings.setExtent(QgsRectangle(-1, -1, 1, 1))
    settings.setMapSettings(map_settings)
    settings.setSceneProperties({'radioButton_WGS84': True})
    settings.updateLayers()
    next(layer for layer in settings.layers() if layer.layerId.startswith('fp:')).visible = True
    settings.localMode = not PLUGIN_VERSION.startswith('3.')
    if PLUGIN_VERSION == '2.8': settings.jsonSerializable = True
    else: settings.requiresJsonSerializable = True
    filename = Path(directory) / 'index.html'
    ThreeJSExporter(settings=settings).export(str(filename))
    html = filename.read_text(encoding='utf-8')
    scripts = list(Path(directory).glob('q3d_decimal_coordinates_*.js'))
    assert len(scripts) == 1 and scripts[0].name in html
    script = scripts[0].read_text(encoding='utf-8')
    assert 'Export heading' in script and 'data:image/svg+xml;base64,' in script
    probe = '''<script>window.addEventListener("load", function () {setTimeout(function () {
      try {
        var app=(window.__qgis2threejs && window.__qgis2threejs.app) || window.app;
        var canvas = app.renderer.domElement, box = canvas.getBoundingClientRect();
        var x=box.left+box.width/2, y=box.top+box.height/2;
        app.canvasClicked({button:0,clientX:x,clientY:y});
        var coords=document.getElementById("qr_coords").textContent;
        var checkbox=document.querySelector('input[aria-label="Show decimal coordinates"]');
        var heading=document.body.textContent.indexOf("Export heading")>=0;
        var arrow=!!document.querySelector('img[alt="North arrow"]');
        var image=document.querySelector('img[alt="North arrow"]');
        var before=image && image.style.transform;
        app.camera.position.x += 10;
        app.controls.dispatchEvent({type:'change'});
        var rotated=!!image && before !== image.style.transform;
        if (checkbox) {checkbox.checked=false; checkbox.dispatchEvent(new Event("change"));}
        var restored=document.getElementById("qr_coords").textContent;
        document.body.setAttribute("data-details", JSON.stringify({coords:coords,restored:restored,heading:heading,arrow:arrow,rotated:rotated,checkbox:!!checkbox,adapter:typeof window.__q3dQueryAdapter,core:typeof window.__qgis2threejs}));
        document.body.setAttribute("data-test", coords.indexOf("° N, ")>=0 && restored.indexOf("′")>=0 && heading && arrow && rotated ? "pass" : "fail");
      } catch(e) { document.body.setAttribute("data-error", String(e)); }
    },1500);});</script>'''
    filename.write_text(html.replace('</body>', probe + '</body>'), encoding='utf-8')
    chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    if os.path.exists(chrome):
        server = None
        url = filename.as_uri()
        if PLUGIN_VERSION.startswith('3.'):
            handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=directory)
            server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            url = 'http://127.0.0.1:{}/index.html'.format(server.server_port)
        try:
            run = subprocess.run([chrome, '--headless', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
                '--no-sandbox', '--allow-file-access-from-files', '--virtual-time-budget=6000',
                '--window-size=1000,800', '--user-data-dir=' + str(Path(directory) / 'chrome-profile'),
                '--dump-dom', url], capture_output=True, timeout=45)
        finally:
            if server: server.shutdown(); server.server_close()
        page = run.stdout.decode('utf-8', errors='replace')
        details = re.search(r'data-(details|error)="[^"]*"', page)
        assert run.returncode == 0 and 'data-test="pass"' in page, details.group(0) if details else run.stderr.decode('utf-8', errors='replace')[-1000:]
        print('Export opened in Chrome: heading, arrow and coordinate toggle passed.')
    else:
        print('Chrome was unavailable; browser rendering was not tested.')
    companion.remove_export_hook()
    print('Real Qgis2threejs {} export hook included heading and embedded north arrow.'.format(PLUGIN_VERSION))
    app.exitQgis()
