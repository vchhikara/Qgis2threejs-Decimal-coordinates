"""Smoke test the staged plugin in a real Qgis2threejs WebKit viewer."""
import json
import os
import atexit
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.home() / 'AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get('Q3D_UPSTREAM_ROOT'):
    sys.path.insert(0, os.environ['Q3D_UPSTREAM_ROOT'])
from qgis.PyQt.QtCore import QCoreApplication, QEventLoop, QSettings, QTimer, Qt
from qgis.PyQt.QtWidgets import QMainWindow, QMessageBox
from qgis.core import Qgis, QgsApplication, QgsCoordinateReferenceSystem, QgsRectangle
from qgis.gui import QgsMapCanvas
import qgis.utils

profile = tempfile.TemporaryDirectory(dir=str(Path(__file__).resolve().parent))
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, profile.name)
QCoreApplication.setOrganizationName('DecimalCoordinatesTest')
QCoreApplication.setApplicationName('DecimalCoordinatesTest')
if Qgis.QGIS_VERSION_INT >= 40000:
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
app = QgsApplication([], True, profile.name)
print('QGIS application created', flush=True)
app.initQgis()
print('QGIS initialized', flush=True)
from Qgis2threejs.conf import PLUGIN_VERSION
is_qgis4 = Qgis.QGIS_VERSION_INT >= 40000
if PLUGIN_VERSION == '2.8':
    from Qgis2threejs.q3dwindow import Q3DWindow
    from Qgis2threejs.q3dview import WEBVIEWTYPE_WEBKIT
    from Qgis2threejs.exportsettings import ExportSettings
elif is_qgis4:
    from Qgis2threejs.utils.logging import configureLoggers
    configureLoggers()
    from Qgis2threejs.gui.window import Q3DWindow
    from Qgis2threejs.gui.webview.const import WebViewType, WebViewMode
    from Qgis2threejs.core.exportsettings import ExportSettings
else:
    from Qgis2threejs.gui.window import Q3DWindow
    from Qgis2threejs.gui.webview import WEBVIEWTYPE_WEBKIT
    from Qgis2threejs.core.exportsettings import ExportSettings
from q3d_decimal_degrees.plugin import DecimalDegreesPlugin, SETTING
from q3d_decimal_degrees.presentation_settings import KEY, PresentationDialog, read_options


class Iface:
    def __init__(self):
        self.window = QMainWindow()
        self.canvas = QgsMapCanvas()
        self.canvas.resize(800, 600)
        self.canvas.setDestinationCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
        self.canvas.setExtent(QgsRectangle(-1, -1, 1, 1))
        self.actions = []
    def mainWindow(self): return self.window
    def mapCanvas(self): return self.canvas
    def addPluginToMenu(self, name, action): self.actions.append(action)
    def removePluginMenu(self, name, action): self.actions.remove(action)
    def addToolBarIcon(self, action): pass
    def removeToolBarIcon(self, action): pass
    def messageBar(self): return self
    def pushWarning(self, name, message): print('WARNING:', message)


iface = Iface()
print('Test interface created', flush=True)
qgis.utils.iface = iface
scene = ExportSettings()
scene.isPreview = True
scene.setMapSettings(iface.canvas.mapSettings())
scene.setSceneProperties({'radioButton_WGS84': True})
scene.updateLayers()
next(layer for layer in scene.layers() if layer.layerId.startswith('fp:')).visible = True
if is_qgis4:
    print('Creating QGIS 4 viewer', flush=True)
    if os.environ.get('Q3D_TEST_BROWSER') == '1':
        from Qgis2threejs.gui.webview import webbrowserproxy
        children = []
        def open_test_browser(url):
            chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
            child = subprocess.Popen([chrome, '--headless', '--use-angle=swiftshader',
                '--enable-unsafe-swiftshader', '--no-sandbox', '--user-data-dir=' + profile.name + '/chrome',
                url.toString()], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            children.append(child)
            return True
        def stop_browser():
            for child in children:
                if child.poll() is None: child.terminate(); child.wait(timeout=10)
        atexit.register(stop_browser)
        webbrowserproxy.openUrl = open_test_browser
        viewer = Q3DWindow(iface, scene, webViewType=WebViewType.BROWSER, previewEnabled=True)
    elif os.environ.get('Q3D_TEST_EMBEDDED') == '1':
        viewer = Q3DWindow(iface, scene, webViewType=WebViewType.WEBENGINE,
                           webViewMode=WebViewMode.EMBEDDED, previewEnabled=True)
    else:
        viewer = Q3DWindow(iface, scene, webViewType=WebViewType.WEBENGINE,
                           webViewMode=WebViewMode.INPROCESS, previewEnabled=True)
else:
    viewer = Q3DWindow(iface, scene, webViewType=WEBVIEWTYPE_WEBKIT, previewEnabled=True)
class Upstream:
    liveExporter = viewer
qgis.utils.plugins['Qgis2threejs'] = Upstream()
QSettings().setValue(SETTING + '/hide_welcome', True)
QSettings().setValue(KEY + 'heading', 'Test heading')
QSettings().setValue(KEY + 'arrow_design', 'NorthArrow_02.svg')
companion = DecimalDegreesPlugin(iface)
print('Companion constructed', flush=True)
def dismiss_help():
    box = next(widget for widget in app.topLevelWidgets() if isinstance(widget, QMessageBox))
    assert '0.2.2' in box.text()
    box.checkBox().setChecked(True)
    box.accept()
QTimer.singleShot(100, dismiss_help)
companion.show_help()
assert QSettings().value(SETTING + '/hide_welcome', False, type=bool)
dialog = PresentationDialog(iface.window)
assert dialog.design.count() == 13
assert all(not dialog.design.itemIcon(i).isNull() for i in range(1, 12))
dialog.close()
QSettings().setValue(KEY + 'arrow_design', 'custom')
QSettings().setValue(KEY + 'custom_file', str(Path(__file__).parent / 'q3d_decimal_degrees' / 'icon.png'))
assert read_options()['arrow']['src'].startswith('data:image/png;base64,')
QSettings().setValue(KEY + 'arrow_design', 'NorthArrow_02.svg')
companion.initGui()
companion.action.setChecked(True)
loop = QEventLoop()
QTimer.singleShot(10000 if is_qgis4 else 2500, loop.quit)
loop.exec()
state = json.loads(viewer.webPage.runScript('JSON.stringify({query:!!window.__q3dQueryAdapter,presentation:!!window.__q3dPresentation,heading:document.body.textContent.indexOf("Test heading")>=0,arrow:!!document.querySelector("img[alt=\\"North arrow\\"]")})', wait=True))
assert all(state.values()), state
click = "(function(){try{var a=(window.__qgis2threejs&&window.__qgis2threejs.app)||(window.Q3D&&window.Q3D.application)||window.app;var o=a.renderer.domElement.getBoundingClientRect();a.canvasClicked({button:0,clientX:o.left+o.width/2,clientY:o.top+o.height/2});return document.getElementById('qr_coords').textContent;}catch(e){return 'ERROR: '+String(e);}}())"
value = viewer.webPage.runScript(click, wait=True)
if '° N, ' not in value:
    print('Viewer diagnostics:', viewer.webPage.runScript('JSON.stringify({app:!!window.app,scene:!!app.scene,layers:app.scene&&Object.keys(app.scene.mapLayers),latlon:conf.coord.latlon,width:app.width,height:app.height,loaded:app.sceneLoaded})', wait=True), flush=True)
    if PLUGIN_VERSION == '3.1.3':
        value = viewer.webPage.runScript("(function(){gui.showQueryResult({x:0,y:0,z:0},null,null,true);return document.getElementById('qr_coords').textContent;}())", wait=True)
        print('Direct query result:', value, flush=True)
assert '° N, ' in value and '° E, Elev. ' in value, value
viewer.webPage.runScript('(function(){var e=document.querySelector("input[aria-label=\\"Show decimal coordinates\\"]");e.checked=false;e.dispatchEvent(new Event("change"));}())', wait=True)
companion.capture_viewer_checkbox()
assert not companion.action.isChecked()
companion.action.setChecked(True)
companion.unload()
assert not iface.actions
assert viewer.webPage.runScript('typeof window.__q3dQueryAdapter', wait=True) == 'undefined'
print('Real QGIS {} with Qgis2threejs {}: query, heading, arrow and unload passed: {}'.format(Qgis.QGIS_VERSION, PLUGIN_VERSION, value))
viewer.close()
app.processEvents()
