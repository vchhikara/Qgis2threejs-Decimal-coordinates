"""Browser-level check using the actual Qgis2threejs 3.2.1 and 3.3 bundles."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class ActualViewerModules(unittest.TestCase):
    def test_real_viewer_query_adapters(self):
        root = Path(__file__).parent
        chrome = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
        if not chrome.exists(): self.skipTest('Chrome is not installed')
        query = (root / 'q3d_decimal_degrees' / 'viewer_query.js').read_text(encoding='utf-8')
        for label, folder in [('3.2.1', 'qgis2threejs_321_test'), ('3.3', 'qgis2threejs_33_test')]:
            with self.subTest(version=label), tempfile.TemporaryDirectory(dir=root) as directory:
                upstream = root / folder / 'Qgis2threejs' / 'web' / 'js'
                if not upstream.exists(): self.skipTest('Upstream package was not downloaded')
                target = Path(directory)
                shutil.copyfile(upstream / 'dist' / 'Qgis2threejs.js', target / 'Qgis2threejs.js')
                shutil.copytree(upstream / 'lib' / 'three', target / 'three')
                runner = '(function(){var n=0;function run(){var result=' + query + ';if(result==="unsupported"&&++n<40)setTimeout(run,100);}run();}());'
                (target / 'adapter.js').write_text(runner, encoding='utf-8')
                (target / 'index.html').write_text('''<!doctype html><html><head>
<script type="importmap">{"imports":{"three":"./three/three.module.js","three/addons/":"./three/"}}</script></head><body>
<table id="qr_coords_table"><tr><td id="qr_coords"></td></tr></table>
<script>window.proj4=function(){return {inverse:function(){return [77,28]}}}</script>
<script type="module">import {app,conf,gui} from "./Qgis2threejs.js";
app.scene={userData:{proj:'x'},toMapCoordinates:()=>({x:1,y:2,z:3})}; conf.coord.latlon=true;
gui.popup.show=()=>{}; window.testCore={app,conf,gui};</script>
<script src="./adapter.js"></script><script>setTimeout(function(){try{
  window.testCore.gui.showQueryResult({},null,null,true);
  var c=document.querySelector('input[aria-label="Show decimal coordinates"]');
  var v=document.getElementById('qr_coords').textContent;
  document.body.setAttribute('data-result',c&&v.indexOf('28.000000° N, 77.000000° E')===0?'pass':'fail');
}catch(e){document.body.setAttribute('data-error',String(e));}},1500);</script></body></html>''', encoding='utf-8')
                result = subprocess.run([str(chrome), '--headless', '--no-sandbox', '--allow-file-access-from-files',
                    '--virtual-time-budget=4000', '--user-data-dir=' + str(target / 'profile'), '--dump-dom',
                    (target / 'index.html').as_uri()], capture_output=True, timeout=45)
                page = result.stdout.decode('utf-8', errors='replace')
                self.assertEqual(result.returncode, 0)
                self.assertIn('data-result="pass"', page, page[:2000])


if __name__ == '__main__': unittest.main()
