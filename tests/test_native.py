"""Native test: load the plugin in real QGIS, toggle it, and unload it."""
import os, sys
from unittest import mock
import pytest

qgis_core = pytest.importorskip('qgis.core')
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QWidget

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture(scope='module')
def app():
    a = QgsApplication([], False)
    a.initQgis()
    yield a
    a.exitQgis()

def test_load_toggle_unload(app):
    import importlib.util
    spec = importlib.util.spec_from_file_location('q3d_dd', os.path.join(ROOT, '__init__.py'),
                                                  submodule_search_locations=[ROOT])
    mod = importlib.util.module_from_spec(spec)
    sys.modules['q3d_dd'] = mod
    spec.loader.exec_module(mod)
    window = QWidget()
    iface = mock.MagicMock()
    iface.mainWindow.return_value = window
    plugin = mod.classFactory(iface)
    plugin.initGui()
    assert plugin.action.isCheckable()
    plugin.action.setChecked(True)
    plugin.action.setChecked(False)
    plugin.unload()
    iface.removeToolBarIcon.assert_called_once()
