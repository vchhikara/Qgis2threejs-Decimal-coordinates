const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const code = fs.readFileSync(__dirname + '/q3d_decimal_degrees/viewer_presentation.js', 'utf8');
const nodes = [];
const body = {appendChild(n) {nodes.push(n); n.parentNode=this;}, removeChild(n) {nodes.splice(nodes.indexOf(n),1); n.parentNode=null;}};
const document = {body, createElement(tag) {return {tag, style:{}, parentNode:null};}};
const controls = {target:{x:0,y:10}, addEventListener(n,cb) {this.cb=cb;}, removeEventListener() {this.cb=null;}};
const app={controls, camera:{position:{x:0,y:0}}, scene:{userData:{proj:'test'},toMapCoordinates:p=>p}};
const root={document,__qgis2threejs:{app},__q3dPresentationOptions:{
  heading:{text:'Scene',size:30,bold:true,italic:true,color:'#12abef'},
  arrow:{src:'data:image/png;base64,AA==',size:70,position:'left'}},
  proj4:()=>({inverse:()=>[0,0],forward:()=>[10,20]})};
assert.equal(vm.runInNewContext(code,{window:root,isFinite}), 'installed');
assert.equal(nodes.length,2);
assert.equal(nodes[0].textContent,'Scene');
assert.equal(nodes[0].style.fontSize,'30px');
assert.equal(nodes[1].style.left,'12px');
const original=nodes[1].style.transform;
assert(original.startsWith('rotate('));
app.camera.position.x=10;
controls.cb();
assert.notEqual(nodes[1].style.transform,original);
root.__q3dPresentation.remove();
assert.equal(nodes.length,0);
assert.equal(controls.cb,null);
console.log('Presentation options, rotation, projection and teardown passed.');
