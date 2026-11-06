import os

from qgis.PyQt.QtCore import QSettings, QTimer
from qgis.PyQt.QtGui import QIcon
try:
    from qgis.PyQt.QtWidgets import QAction
except ImportError:  # Qt 6
    from qgis.PyQt.QtGui import QAction
from qgis.core import Qgis, QgsMessageLog
import qgis.utils

from .export_support import prepare_export

NAME = 'Qgis2threejs Decimal Coordinates'
SETTING = '/Qgis2threejsDecimalDegrees/enabled'
REMOVE = "if (window.__q3dDecimalDegreesCompanion) window.__q3dDecimalDegreesCompanion.remove();"


class DecimalDegreesPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.page = None
        self.exporter_class = None
        self.original_export = None
        self.wrapper = None
        self.hook_active = False
        self.running = True
        self.timer = None
        self.warned = set()
        with open(os.path.join(os.path.dirname(__file__), 'decimal_degrees.js'), encoding='utf-8') as file:
            self.javascript = file.read()

    def log(self, message, warning=False):
        QgsMessageLog.logMessage(message, NAME, Qgis.MessageLevel.Warning if warning else Qgis.MessageLevel.Info)

    def warn_once(self, message):
        if message not in self.warned:
            self.warned.add(message)
            self.log(message, True)
            self.iface.messageBar().pushWarning(NAME, message)

    def initGui(self):
        icon = QIcon(os.path.join(os.path.dirname(__file__), 'icon.png'))
        self.action = QAction(icon, 'Decimal degree coordinates', self.iface.mainWindow())
        self.action.setToolTip('Toggle decimal degree coordinates in Qgis2threejs')
        self.action.setCheckable(True)
        self.action.setChecked(QSettings().value(SETTING, False, type=bool))
        self.action.toggled.connect(self.toggle)
        self.iface.addPluginToMenu(NAME, self.action)
        self.iface.addToolBarIcon(self.action)
        self.timer = QTimer(self.iface.mainWindow())
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1500)
        self.refresh()

    def toggle(self, enabled):
        QSettings().setValue(SETTING, enabled)
        self.apply_to_page()

    def apply_to_page(self, *args):
        if self.page:
            try:
                page = self.page
                if self.action.isChecked():
                    def checked(result):
                        if result == 'unsupported':
                            QTimer.singleShot(1500, lambda: self.verify_page(page))
                        elif result == 'invalid-current' and self.running and self.page is page:
                            self.warn_once('The current coordinate text could not be parsed; it was left unchanged.')
                    page.runScript(self.javascript, sourceID=NAME, callback=checked)
                else:
                    page.runScript(REMOVE, sourceID=NAME)
            except RuntimeError:
                self.page = None

    def verify_page(self, page):
        if not self.running or self.page is not page or not self.action.isChecked():
            return
        def checked(result):
            if result == 'unsupported' and self.running and self.page is page and self.action.isChecked():
                self.warn_once('The viewer coordinate display could not be found; decimal degree display is inactive.')
        try:
            page.runScript(self.javascript, sourceID=NAME, callback=checked)
        except RuntimeError:
            pass

    def refresh(self):
        plugin = qgis.utils.plugins.get('Qgis2threejs')
        if plugin is None:
            self.detach_page()
            self.remove_export_hook()
            return
        try:
            from Qgis2threejs.conf import PLUGIN_VERSION
            if PLUGIN_VERSION != '2.10.2':
                self.warn_once('Unsupported Qgis2threejs version {}; expected 2.10.2. Companion is inactive.'.format(PLUGIN_VERSION))
                self.detach_page()
                self.remove_export_hook()
                return
            from Qgis2threejs.core.export.export import ThreeJSExporter
            if self.exporter_class is None:
                self.install_export_hook(ThreeJSExporter)
            viewer = plugin.liveExporter
            page = viewer.webPage if viewer else None
            if page is not self.page:
                self.detach_page()
                self.page = page
                if page:
                    page.loadFinished.connect(self.apply_to_page)
                    self.apply_to_page()
        except (AttributeError, ImportError, RuntimeError) as error:
            self.warn_once('Could not connect to Qgis2threejs: {}'.format(error))

    def install_export_hook(self, cls):
        original = cls.export
        companion = self
        self.hook_active = True
        def export(exporter, filename=None, abortSignal=None):
            enabled = companion.hook_active and companion.action.isChecked()
            result = original(exporter, filename, abortSignal)
            if enabled:
                try:
                    prepare_export(exporter.settings.outputFileName(), companion.javascript)
                except Exception as error:
                    companion.log('Export was generated but decimal degree integration failed: {}'.format(error), True)
                    raise RuntimeError('Decimal degree export integration failed: {}'.format(error)) from error
            return result
        self.exporter_class, self.original_export, self.wrapper = cls, original, export
        cls.export = export

    def detach_page(self):
        if self.page:
            try:
                self.page.runScript(REMOVE, sourceID=NAME)
                self.page.loadFinished.disconnect(self.apply_to_page)
            except (RuntimeError, TypeError):
                pass
            self.page = None

    def unload(self):
        self.running = False
        self.timer.stop()
        self.detach_page()
        self.remove_export_hook()
        self.iface.removePluginMenu(NAME, self.action)
        self.iface.removeToolBarIcon(self.action)

    def remove_export_hook(self):
        self.hook_active = False
        if self.exporter_class and self.exporter_class.export is self.wrapper:
            self.exporter_class.export = self.original_export
        elif self.exporter_class:
            self.log('Export hook was replaced by another extension and could not be restored safely.', True)
        self.exporter_class = self.original_export = self.wrapper = None
