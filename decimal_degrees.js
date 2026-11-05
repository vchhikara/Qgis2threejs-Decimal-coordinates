(function (root) {
  'use strict';
  var key = '__q3dDecimalDegreesCompanion';
  if (root[key]) return 'already-installed';
  var utils = root.Q3D && root.Q3D.Utils;
  var element = root.document && root.document.getElementById('qr_coords');
  if (!utils || typeof utils.convertToDMS !== 'function' || !element) {
    if (root.console) root.console.warn('Decimal Degrees: unsupported viewer structure');
    return 'unsupported';
  }
  var original = utils.convertToDMS;
  var enabled = true;
  var latestOriginal = null, latestDecimal = null;
  // The current selection predates installation; its DMS text has already been rounded.
  var current = element.textContent;
  var match = /^([NS])(\d+)°(\d{2})′(\d{2}(?:\.\d+)?)″, ([EW])(\d+)°(\d{2})′(\d{2}(?:\.\d+)?)″(, Elev\. .*)$/.exec(current);
  var invalidCurrent = false;
  if (match) {
    var lat = +match[2] + +match[3] / 60 + +match[4] / 3600;
    var lon = +match[6] + +match[7] / 60 + +match[8] / 3600;
    if (+match[3] < 60 && +match[4] <= 60 && +match[7] < 60 && +match[8] <= 60 && lat <= 90 && lon <= 180) {
      latestOriginal = current.slice(0, current.length - match[9].length);
      latestDecimal = ((match[1] === 'S' ? -lat : lat) || 0).toFixed(6) + '° N, ' + ((match[5] === 'W' ? -lon : lon) || 0).toFixed(6) + '° E';
      element.textContent = latestDecimal + match[9];
    }
    else invalidCurrent = true;
  }
  else if (/^[NS]\d/.test(current)) invalidCurrent = true;
  if (invalidCurrent && root.console) root.console.warn('Decimal Degrees: existing coordinate is invalid; preserving original');
  function format(lat, lon) {
    var dms = original.apply(this, arguments);
    // Another extension may retain this wrapper after our hook is removed.
    if (!enabled) return dms;
    if (typeof lat !== 'number' || typeof lon !== 'number' ||
        !isFinite(lat) || !isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) {
      if (root.console) root.console.warn('Decimal Degrees: invalid geographic coordinate; preserving original');
      latestOriginal = latestDecimal = null;
      return dms;
    }
    latestOriginal = dms;
    latestDecimal = (lat === 0 ? 0 : lat).toFixed(6) + '° N, ' + (lon === 0 ? 0 : lon).toFixed(6) + '° E';
    return latestDecimal;
  }
  utils.convertToDMS = format;
  root[key] = {
    remove: function () {
      enabled = false;
      if (utils.convertToDMS === format) utils.convertToDMS = original;
      else if (root.console) root.console.warn('Decimal Degrees: formatter changed by another extension; cannot restore it');
      var text = element.textContent;
      if (latestDecimal && text.indexOf(latestDecimal + ', Elev. ') === 0) {
        element.textContent = latestOriginal + text.slice(latestDecimal.length);
      }
      delete root[key];
    }
  };
  return invalidCurrent ? 'invalid-current' : 'installed';
}(window));
