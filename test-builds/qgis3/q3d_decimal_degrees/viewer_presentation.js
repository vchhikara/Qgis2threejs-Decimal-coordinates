/* Presentation overlay. Configuration is supplied by the plugin or exported scene. */
(function (root) {
  'use strict';
  var key = '__q3dPresentation';
  if (root[key]) root[key].remove();
  var options = root.__q3dPresentationOptions || {};
  var core = root.__qgis2threejs || (root.Q3D && {app: root.Q3D.application}) || (root.app && {app: root.app});
  var document = root.document;
  if (!document || !document.body) return 'unsupported';
  var nodes = [], controls = null, listener = null, app = null;
  function clamp(value, low, high, fallback) {
    value = Number(value);
    return isFinite(value) ? Math.max(low, Math.min(high, value)) : fallback;
  }
  if (options.heading && options.heading.text) {
    var heading = document.createElement('div');
    var h = options.heading;
    heading.textContent = h.text;
    heading.style.cssText = 'position:absolute;top:8px;left:0;width:100%;text-align:center;z-index:20;pointer-events:none;';
    heading.style.fontFamily = h.font || 'sans-serif';
    heading.style.fontSize = clamp(h.size, 8, 96, 24) + 'px';
    heading.style.fontWeight = h.bold ? 'bold' : 'normal';
    heading.style.fontStyle = h.italic ? 'italic' : 'normal';
    heading.style.color = /^#[0-9a-f]{6}$/i.test(h.color || '') ? h.color : '#000000';
    document.body.appendChild(heading);
    nodes.push(heading);
  }
  if (options.arrow && options.arrow.src) {
    var arrow = document.createElement('img');
    var a = options.arrow;
    arrow.alt = 'North arrow';
    arrow.src = a.src;
    arrow.style.cssText = 'position:absolute;z-index:20;pointer-events:none;';
    arrow.style.width = clamp(a.size, 20, 300, 64) + 'px';
    arrow.style.height = 'auto';
    arrow.style.top = '12px';
    arrow.style[a.position === 'left' ? 'left' : 'right'] = '12px';
    document.body.appendChild(arrow);
    nodes.push(arrow);
    // Compare the camera bearing to geographic north near the camera target.
    app = core && core.app;
    controls = app && app.controls;
    if (controls && app.camera && app.scene && app.scene.toMapCoordinates && controls.target) {
      listener = function () {
        try {
          var from = app.scene.toMapCoordinates(app.camera.position);
          var to = app.scene.toMapCoordinates(controls.target);
          var dx = to.x - from.x, dy = to.y - from.y;
          if (isFinite(dx) && isFinite(dy) && (dx || dy)) {
            var northBearing = 0;
            if (typeof root.proj4 === 'function' && app.scene.userData && app.scene.userData.proj) {
              try {
                var projection = root.proj4(app.scene.userData.proj);
                var ll = projection.inverse([to.x, to.y]);
                var step = ll[1] > 89.999 ? -0.0001 : 0.0001;
                var north = projection.forward([ll[0], ll[1] + step]);
                var nx = (north[0] - to.x) * (step < 0 ? -1 : 1);
                var ny = (north[1] - to.y) * (step < 0 ? -1 : 1);
                if (isFinite(nx) && isFinite(ny) && (nx || ny)) northBearing = Math.atan2(nx, ny);
              } catch (error) { /* Use map grid north if projection is unavailable. */ }
            }
            arrow.style.transform = 'rotate(' + ((northBearing - Math.atan2(dx, dy)) * 180 / Math.PI) + 'deg)';
          }
        } catch (error) { /* Scene may still be loading. */ }
      };
      if (controls.addEventListener) controls.addEventListener('change', listener);
      if (app.addEventListener) app.addEventListener('sceneLoaded', listener);
      listener();
    }
  }
  root[key] = {remove: function () {
    if (controls && listener && controls.removeEventListener) controls.removeEventListener('change', listener);
    if (app && listener && app.removeEventListener) app.removeEventListener('sceneLoaded', listener);
    nodes.forEach(function (node) { if (node.parentNode) node.parentNode.removeChild(node); });
    delete root[key];
  }};
  return 'installed';
}(window));
