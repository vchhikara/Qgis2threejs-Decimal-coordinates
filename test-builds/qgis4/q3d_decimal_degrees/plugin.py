import importlib
import json
import os

from qgis.PyQt.QtCore import QSettings, QThread, QTimer
from qgis.PyQt.QtGui import QIcon
try:
    from qgis.PyQt.QtWidgets import QAction
except ImportError:  # Qt 6
    from qgis.PyQt.QtGui import QAction
from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtWidgets import QCheckBox, QDialog, QMessageBox
import qgis.utils

from .presentation_settings import PresentationDialog, read_options
from .scene_export import add_scene_script
from .version_adapter import exporter_module, export_succeeded

NAME = 'Qgis2threejs Decimal Coordinates'
SETTING = '/Qgis2threejsDecimalDegrees/enabled'
REMOVE = "if(window.__q3dQueryAdapter)window.__q3dQueryAdapter.remove();if(window.__q3dPresentation)window.__q3dPresentation.remove();"


class DecimalDegreesPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.settings_action = None
        self.help_action = None
        self.page = None
        self.exporter_class = None
        self.original_export = None
        self.wrapper = None
        self.hook_active = False
        self.running = True
        self.timer = None
        self.warned = set()
        self.action_generation = 0
        self.edition = 4 if Qgis.QGIS_VERSION_INT >= 40000 else 3
        self.release = '0.2.4' if self.edition == 4 else '0.2.3'
        with open(os.path.join(os.path.dirname(__file__), 'viewer_query.js'), encoding='utf-8') as file:
            self.query_javascript = file.read()
        with open(os.path.join(os.path.dirname(__file__), 'viewer_presentation.js'), encoding='utf-8') as file:
            self.presentation_javascript = file.read()

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
        self.settings_action = QAction('Heading and north arrow…', self.iface.mainWindow())
        self.settings_action.triggered.connect(self.show_settings)
        self.iface.addPluginToMenu(NAME, self.settings_action)
        self.help_action = QAction("What's New and help", self.iface.mainWindow())
        self.help_action.triggered.connect(self.show_help)
        self.iface.addPluginToMenu(NAME, self.help_action)
        self.timer = QTimer(self.iface.mainWindow())
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1500)
        self.refresh()
        settings = QSettings()
        if not settings.value(SETTING + '/hide_welcome', False, type=bool) and settings.value(SETTING + '/welcome_version', '', type=str) != self.release:
            QTimer.singleShot(0, self.show_help)

    def show_settings(self):
        dialog = PresentationDialog(self.iface.mainWindow())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dialog.save()
            self.apply_to_page()

    def show_help(self):
        if not self.running: return
        dialog = QMessageBox(self.iface.mainWindow())
        dialog.setWindowTitle("What's New in " + self.release)
        dialog.setText('New since version 0.2.2:')
        dialog.setInformativeText('Use the checkbox beside clicked coordinates to switch decimal display. '
            'Choose Heading and north arrow in the plugin menu to configure a heading or select an arrow, '
            'including your own SVG or PNG. Select Latitude and longitude in Qgis2threejs scene settings. '
            'New web exports include the viewer settings. Reopen this window from the plugin menu.')
        checkbox = QCheckBox("Don't show automatically again")
        dialog.setCheckBox(checkbox)
        dialog.exec()
        settings = QSettings()
        settings.setValue(SETTING + '/welcome_version', self.release)
        if checkbox.isChecked(): settings.setValue(SETTING + '/hide_welcome', True)

    def build_script(self):
        options = json.dumps(read_options(), ensure_ascii=True)
        enabled = 'true' if self.action.isChecked() else 'false'
        return ('(function(){' + REMOVE + 'window.__q3dPresentationOptions=' + options + ';'
                'window.__q3dQueryInitialEnabled=' + enabled + ';' + self.presentation_javascript +
                'var result=' + self.query_javascript + ';return result;}())')

    def toggle(self, enabled):
        self.action_generation += 1
        QSettings().setValue(SETTING, enabled)
        self.apply_to_page()

    def apply_to_page(self, *args):
        if self.page:
            try:
                page = self.page
                def checked(result):
                    if result == 'unsupported': QTimer.singleShot(500, lambda: self.verify_page(page, 0))
                page.runScript(self.build_script(), sourceID=NAME, callback=checked)
            except (OSError, ValueError) as error:
                self.warn_once('Viewer settings could not be loaded: {}'.format(error))
            except RuntimeError:
                self.page = None

    def verify_page(self, page, attempts=0):
        if not self.running or self.page is not page:
            return
        def checked(result):
            if result == 'unsupported' and self.running and self.page is page:
                if attempts < 19:
                    QTimer.singleShot(500, lambda: self.verify_page(page, attempts + 1))
                else:
                    self.warn_once('The viewer coordinate display could not be found; decimal degree display is inactive.')
        try:
            page.runScript(self.build_script(), sourceID=NAME, callback=checked)
        except (RuntimeError, OSError, ValueError):
            pass

    def refresh(self):
        plugin = qgis.utils.plugins.get('Qgis2threejs')
        if plugin is None:
            self.detach_page()
            self.remove_export_hook()
            return
        try:
            from Qgis2threejs.conf import PLUGIN_VERSION
            module = exporter_module(PLUGIN_VERSION, self.edition)
            if not module:
                self.warn_once('Unsupported Qgis2threejs version {}; companion is inactive.'.format(PLUGIN_VERSION))
                self.detach_page()
                self.remove_export_hook()
                return
            ThreeJSExporter = importlib.import_module(module).ThreeJSExporter
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
            elif page:
                self.sync_checkbox(page)
        except (AttributeError, ImportError, RuntimeError) as error:
            self.warn_once('Could not connect to Qgis2threejs: {}'.format(error))

    def sync_checkbox(self, page):
        generation = self.action_generation
        def checked(value):
            if (not self.running or self.page is not page or generation != self.action_generation
                    or not isinstance(value, bool)):
                return
            if value != self.action.isChecked():
                self.action_generation += 1
                previous = self.action.blockSignals(True)
                self.action.setChecked(value)
                self.action.blockSignals(previous)
                QSettings().setValue(SETTING, value)
        page.runScript('window.__q3dQueryAdapter ? window.__q3dQueryAdapter.isChecked() : null',
                       sourceID=NAME, callback=checked)

    def capture_viewer_checkbox(self):
        """Read the current viewer value before exporting, when called on its Qt thread."""
        page = self.page
        if not page: return
        try:
            if QThread.currentThread() != page.thread(): return
            value = page.runScript('window.__q3dQueryAdapter ? window.__q3dQueryAdapter.isChecked() : null',
                                   sourceID=NAME, wait=True)
            if isinstance(value, bool) and value != self.action.isChecked():
                self.action_generation += 1
                previous = self.action.blockSignals(True)
                self.action.setChecked(value)
                self.action.blockSignals(previous)
                QSettings().setValue(SETTING, value)
        except RuntimeError:
            pass

    def install_export_hook(self, cls):
        original = cls.export
        companion = self
        self.hook_active = True
        def export(exporter, *args, **kwargs):
            if companion.hook_active: companion.capture_viewer_checkbox()
            result = original(exporter, *args, **kwargs)
            if companion.hook_active and export_succeeded(result):
                try:
                    script = companion.build_script()
                    # Module-based viewers may initialise after the HTML document finishes loading.
                    runner = ('(function(){var n=0;function run(){var result=' + script + ';'
                              'if(result==="unsupported" && ++n<40)setTimeout(run,250);}run();}());')
                    add_scene_script(exporter.settings.outputFileName(), runner)
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
        self.iface.removePluginMenu(NAME, self.settings_action)
        self.iface.removePluginMenu(NAME, self.help_action)
        self.iface.removeToolBarIcon(self.action)

    def remove_export_hook(self):
        self.hook_active = False
        if self.exporter_class and self.exporter_class.export is self.wrapper:
            self.exporter_class.export = self.original_export
        elif self.exporter_class:
            self.log('Export hook was replaced by another extension and could not be restored safely.', True)
        self.exporter_class = self.original_export = self.wrapper = None
