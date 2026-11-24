"""Unmodified third-party TV APK: code, actual pixels and D-pad interaction.

APK is fetched directly from its author's pinned Git commit, never repackaged or
distributed in PadTV. Source provenance is part of the public compatibility data.
"""
import hashlib,json,os,shutil,subprocess,tempfile,unittest,urllib.request
from pathlib import Path
from PIL import Image
from build_fixtures import ROOT

URL='https://raw.githubusercontent.com/LuoJuly/TV_Screen_4K_Calibration_TEST/ddf6367504568834b0ba70beef561bc6ac5081d6/ScreenTest-4K.apk'
SHA='a68b762262f57ae77ba0faead7499e1907093329b58752bd957b18284446752e'

class OriginalTvApkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.download=tempfile.TemporaryDirectory(prefix='upstream-tv-')
        cls.apk=Path(cls.download.name)/'original.apk'
        with urllib.request.urlopen(URL,timeout=30) as response:body=response.read(1024*1024)
        if hashlib.sha256(body).hexdigest()!=SHA:raise AssertionError('Upstream APK hash changed')
        cls.apk.write_bytes(body)
        if shutil.which('systemctl'):
            service=subprocess.run(['systemctl','is-active','waydroid-container.service'],capture_output=True,text=True)
            if service.stdout.strip()=='active':raise AssertionError('Stop Waydroid before PadBridge compatibility tests')
        elif shutil.which('waydroid'):
            raise AssertionError('Cannot verify Waydroid state on this host')
    @classmethod
    def tearDownClass(cls):cls.download.cleanup()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='original-tv-data-');self.root=Path(self.temp.name)
        self.env={**os.environ,'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime'),'PADBRIDGE_DATA_HOME':str(self.root)}
        self.app=self.call('install',self.apk)['app'];self.data=self.root/'data'/self.app['package']
    def tearDown(self):self.temp.cleanup()
    def call(self,*args):
        p=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],env=self.env,capture_output=True,text=True,timeout=60)
        r=json.loads(p.stdout);self.assertTrue(r['ok'],r);return r
    def execute(self,keys):
        (self.data/'test-keys.txt').write_text(','.join(map(str,keys)))
        r=self.call('run',self.app['package'],'--headless')
        return json.loads(r['output'].split('PADBRIDGE_SCENE=')[1].splitlines()[0])
    def test_original_code_renders_green_and_updates_hud(self):
        stored=self.root/'packages'/self.app['package']/self.app['sha256']/'original.apk'
        self.assertEqual(hashlib.sha256(stored.read_bytes()).hexdigest(),SHA)
        scene=self.execute([22]*3)
        self.assertTrue(any('4/35' in n['text'] for n in scene['nodes']))
        pixels=[]
        for path in self.data.glob('rendered-view-*.png'):
            with Image.open(path) as img:
                if img.height>500:pixels.append(img.convert('RGB').getpixel((500,500)))
        self.assertIn((0,255,0),pixels)
    def test_original_bitmap_shader_checkerboard(self):
        scene=self.execute([22]*12);self.assertTrue(any('13/35' in n['text'] for n in scene['nodes']))
        matches=[]
        for path in self.data.glob('rendered-view-*.png'):
            with Image.open(path) as img:
                if img.height>500:
                    rgb=img.convert('RGB');a,b,c=[rgb.getpixel((x,500)) for x in (500,502,504)]
                    matches.append(a!=b and a==c and {a,b}=={(0,0,0),(255,255,255)})
        self.assertTrue(any(matches),'Actual checkerboard pixels were not rendered')
    def test_original_center_button_hides_controls(self):
        shown=self.execute([]);hidden=self.execute([23])
        self.assertGreater(sum(n['visibility']!=0 for n in hidden['nodes']),sum(n['visibility']!=0 for n in shown['nodes']))

if __name__=='__main__':unittest.main(verbosity=2)
