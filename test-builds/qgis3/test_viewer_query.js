const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(__dirname + '/q3d_decimal_degrees/viewer_query.js', 'utf8');

function fixture(modules) {
  const row = {children: [], insertBefore(node) { node.parentNode = this; this.children.unshift(node); },
    removeChild(node) { this.children.splice(this.children.indexOf(node), 1); node.parentNode = null; }};
  const cell = {textContent: '', parentNode: row};
  row.children.push(cell);
  const document = {
    getElementById() { return cell; },
    createTextNode(text) { return {text}; },
    createElement(tag) { return {tag, style: {}, children: [], appendChild(child) { this.children.push(child); child.parentNode = this; },
      setAttribute() {}, addEventListener(name, handler) { this[name] = handler; }, removeEventListener(name) { delete this[name]; }}; }
  };
  const original = function () { cell.textContent = 'DMS, Elev. 42.00'; return 'result'; };
  const core = {gui: {showQueryResult: original}, conf: {coord: {latlon: true}},
    app: {scene: {toMapCoordinates: () => ({x: 1, y: 2, z: 42}), userData: {proj: 'x'}}}};
  const root = {document, console, proj4: () => ({inverse: () => [-77.1234567, 28.1234567]})};
  if (modules) root.__qgis2threejs = core;
  else root.Q3D = {application: core.app, Config: core.conf, gui: core.gui};
  return {root, row, cell, core, original};
}

for (const modules of [false, true, 'preview-globals']) {
  const f = fixture(modules);
  if (modules === 'preview-globals') {
    delete f.root.__qgis2threejs;
    f.root.app = f.core.app; f.root.gui = f.core.gui; f.root.conf = f.core.conf;
  }
  assert.equal(vm.runInNewContext(source, {window: f.root, isFinite}), 'installed');
  const checkbox = f.row.children[0].children[0].children[0];
  assert.equal(f.core.gui.showQueryResult({}, null, null, true), 'result');
  assert.equal(f.cell.textContent, '28.123457° N, -77.123457° E, Elev. 42.00');
  checkbox.checked = false; checkbox.change();
  assert.equal(f.cell.textContent, 'DMS, Elev. 42.00');
  checkbox.checked = true; checkbox.change();
  assert.equal(f.cell.textContent, '28.123457° N, -77.123457° E, Elev. 42.00');
  f.core.conf.coord.latlon = false;
  f.core.gui.showQueryResult({}, null, null, true);
  assert.equal(f.cell.textContent, 'DMS, Elev. 42.00');
  f.root.__q3dQueryAdapter.remove();
  assert.strictEqual(f.core.gui.showQueryResult, f.original);
  assert.equal(f.row.children.length, 1);
}
for (const [source, expected] of [
  ['import * as exports from "./js/dist/preview.js";', './js/dist/preview.js'],
  ['import { app } from "./Qgis2threejs.js";', './Qgis2threejs.js']
]) {
  const f = fixture(true);
  delete f.root.__qgis2threejs;
  const added = [];
  f.root.document.querySelectorAll = () => [{textContent: source}];
  f.root.document.head = {appendChild(node) { added.push(node); }};
  assert.equal(vm.runInNewContext(sourceFile(), {window: f.root, isFinite}), 'unsupported');
  assert.equal(added.length, 1);
  assert.equal(added[0].type, 'module');
  assert(added[0].textContent.includes(expected));
  vm.runInNewContext(sourceFile(), {window: f.root, isFinite});
  assert.equal(added.length, 1);
}
function sourceFile() { return fs.readFileSync(__dirname + '/q3d_decimal_degrees/viewer_query.js', 'utf8'); }
console.log('Both viewer adapters, checkbox, projected coordinates and teardown passed.');
