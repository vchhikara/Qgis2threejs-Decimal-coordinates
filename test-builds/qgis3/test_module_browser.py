"""Exercise 3.2-style module bootstrap in a browser without QGIS 4."""
import html
from pathlib import Path
import subprocess
import tempfile
import unittest


class ModuleViewerTest(unittest.TestCase):
    def test_module_viewer_bootstrap_and_checkbox(self):
        chrome = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
        if not chrome.exists(): self.skipTest('Chrome is not installed')
        source = (Path(__file__).parent / 'q3d_decimal_degrees' / 'viewer_query.js').read_text(encoding='utf-8')
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            folder = Path(directory)
            (folder / 'Qgis2threejs.js').write_text('''
export const conf={coord:{latlon:true}};
export const app={scene:{userData:{proj:'x'},toMapCoordinates:()=>({x:1,y:2,z:3})}};
export const gui={showQueryResult:function(){document.getElementById('qr_coords').textContent='DMS, Elev. 3.00';}};
''', encoding='utf-8')
            runner = '(function(){var n=0;function run(){var result=' + source + ';if(result==="unsupported"&&++n<40)setTimeout(run,100);}run();}());'
            (folder / 'adapter.js').write_text(runner, encoding='utf-8')
            (folder / 'index.html').write_text('''<!doctype html><html><head></head><body>
<table><tr><td id="qr_coords"></td></tr></table>
<script>window.proj4=function(){return {inverse:function(){return [77,28]}}}</script>
<script type="module">import {app} from "./Qgis2threejs.js";</script>
<script src="./adapter.js"></script>
<script>setTimeout(function(){
 if(window.__qgis2threejs){window.__qgis2threejs.gui.showQueryResult({},null,null,true);}
 var c=document.querySelector('input[aria-label="Show decimal coordinates"]');
 document.body.setAttribute('data-result',c && document.getElementById('qr_coords').textContent.indexOf('28.000000° N')===0?'pass':'fail');
},1000);</script></body></html>''', encoding='utf-8')
            result = subprocess.run([str(chrome), '--headless', '--no-sandbox', '--allow-file-access-from-files',
                '--virtual-time-budget=3000', '--user-data-dir=' + str(folder / 'profile'), '--dump-dom',
                (folder / 'index.html').as_uri()], capture_output=True, timeout=45)
            page = result.stdout.decode('utf-8', errors='replace')
            self.assertEqual(result.returncode, 0)
            self.assertIn('data-result="pass"', html.unescape(page))


if __name__ == '__main__': unittest.main()
