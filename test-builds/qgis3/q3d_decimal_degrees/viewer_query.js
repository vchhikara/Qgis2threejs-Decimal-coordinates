/* Geographic query display adapter for legacy and module-based viewers. */
(function (root) {
  'use strict';
  var key = '__q3dQueryAdapter';
  if (root[key]) return 'already-installed';
  var core = root.__qgis2threejs || (root.Q3D && {
    app: root.Q3D.application, gui: root.Q3D.gui, conf: root.Q3D.Config
  }) || (root.app && root.gui && root.conf && {app: root.app, gui: root.gui, conf: root.conf});
  // Qgis2threejs 3.2 exports these objects as modules, but does not expose
  // them on window. Reuse the viewer's own module so we get the same objects.
  if (!core && root.document && !root.__q3dModuleLoading) {
    var scripts = root.document.querySelectorAll('script[type="module"]');
    var modulePath = null;
    for (var i = 0; i < scripts.length; i++) {
      var text = scripts[i].textContent || '';
      if (text.indexOf('./js/dist/preview.js') >= 0) modulePath = './js/dist/preview.js';
      else if (text.indexOf('./Qgis2threejs.js') >= 0) modulePath = './Qgis2threejs.js';
    }
    if (modulePath) {
      root.__q3dModuleLoading = true;
      var bootstrap = root.document.createElement('script');
      bootstrap.type = 'module';
      bootstrap.textContent = 'import * as core from "' + modulePath + '"; window.__qgis2threejs = core;';
      root.document.head.appendChild(bootstrap);
    }
  }
  var cell = root.document && root.document.getElementById('qr_coords');
  if (!core || !core.gui || !core.app || !core.conf || !cell ||
      typeof core.gui.showQueryResult !== 'function') return 'unsupported';

  var original = core.gui.showQueryResult, active = true;
  var latestOriginal = null, latestDecimal = null;
  var controlCell = root.document.createElement('td');
  var label = root.document.createElement('label');
  var check = root.document.createElement('input');
  check.type = 'checkbox';
  check.checked = root.__q3dQueryInitialEnabled !== false;
  check.setAttribute('aria-label', 'Show decimal coordinates');
  label.appendChild(check);
  label.appendChild(root.document.createTextNode(' Decimal degrees'));
  label.style.whiteSpace = 'nowrap';
  controlCell.appendChild(label);
  cell.parentNode.insertBefore(controlCell, cell);

  function update() {
    if (latestDecimal === null) return;
    cell.textContent = check.checked ? latestDecimal : latestOriginal;
  }
  check.addEventListener('change', update);

  function wrapped(point, layer, object, showCoords) {
    var result = original.apply(this, arguments);
    latestOriginal = latestDecimal = null;
    if (!active || !showCoords || !core.conf.coord || !core.conf.coord.latlon ||
        typeof root.proj4 !== 'function') return result;
    try {
      var pt = core.app.scene.toMapCoordinates(point);
      var lonLat = root.proj4(core.app.scene.userData.proj).inverse([pt.x, pt.y]);
      var lon = lonLat[0], lat = lonLat[1];
      if (typeof lat !== 'number' || typeof lon !== 'number' ||
          !isFinite(lat) || !isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) return result;
      latestOriginal = cell.textContent;
      latestDecimal = (lat === 0 ? 0 : lat).toFixed(6) + '° N, ' +
        (lon === 0 ? 0 : lon).toFixed(6) + '° E, Elev. ' + pt.z.toFixed(2);
      update();
    } catch (error) {
      if (root.console) root.console.warn('Decimal Coordinates:', error);
    }
    return result;
  }

  core.gui.showQueryResult = wrapped;
  root[key] = {isChecked: function () { return check.checked; }, remove: function () {
    active = false;
    if (latestOriginal !== null && cell.textContent === latestDecimal) cell.textContent = latestOriginal;
    if (core.gui.showQueryResult === wrapped) core.gui.showQueryResult = original;
    check.removeEventListener('change', update);
    if (controlCell.parentNode) controlCell.parentNode.removeChild(controlCell);
    delete root[key];
  }};
  return 'installed';
}(window));
