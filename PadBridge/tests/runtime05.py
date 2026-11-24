"""0.2 integration: original Java/Kotlin DEX, resources, storage and split sets."""
import hashlib,json,os,subprocess,tempfile,unittest,zipfile
from pathlib import Path
from build_fixtures import ROOT,OUT

class Runtime05Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='padbridge05-');self.root=Path(self.temp.name)
        self.env={**os.environ,'PADBRIDGE_DATA_HOME':str(self.root),'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
    def tearDown(self):self.temp.cleanup()
    def call(self,*args,ok=True):
        p=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],env=self.env,capture_output=True,text=True,timeout=150)
        try:r=json.loads(p.stdout)
        except ValueError:self.fail(p.stdout+p.stderr)
        self.assertEqual(r['ok'],ok,r);return r
    def install(self,name):return self.call('install',OUT/name)['app']
    def keys(self,app,keys='23'):(self.root/'data'/app['package']/'test-keys.txt').write_text(keys)
    def test_java_multidex_xml_sqlite_threads_reflection_and_local_binder(self):
        meta=self.call('inspect',OUT/'java-multidex.apk');self.assertEqual(meta['diagnostics']['dex_files'],2);self.assertIn('038',meta['diagnostics']['dex_versions'])
        app=self.install('java-multidex.apk');self.keys(app)
        r=self.call('run',app['package'],'--headless')
        for marker in ['JAVA_SQLITE_PREFS_THREADS_REFLECTION_BINDER_MULTIDEX_OK','HANDLER_OK','BROADCAST_OK','XML_DPAD_OK','SERVICE_STARTED_42','SERVICE_STOPPED','CONTENT_PROVIDER_OK']:self.assertIn(marker,r['output'])
        self.assertIn('runs=1',r['output']);r=self.call('run',app['package'],'--headless');self.assertIn('runs=2',r['output'])
    def test_kotlin_original_dex_and_click(self):
        app=self.install('kotlin.apk');self.keys(app)
        r=self.call('run',app['package'],'--headless');self.assertIn('KOTLIN_ORIGINAL_DEX_OK',r['output']);self.assertIn('KOTLIN_DPAD_OK',r['output'])
    def test_split_set_executes_feature_dex_and_preserves_original_files(self):
        app=self.call('install-set',OUT/'split-feature.apk',OUT/'split-base.apk')['app'];self.assertEqual(len(app['splits']),1)
        folder=self.root/'packages'/app['package']/app['installation_id']
        self.assertEqual((folder/'original.apk').read_bytes(),(OUT/'split-base.apk').read_bytes())
        self.assertEqual((folder/'splits/feature.code.apk').read_bytes(),(OUT/'split-feature.apk').read_bytes())
        self.assertIn('MULTIDEX_OK',self.call('run',app['package'],'--headless')['output'])
    def test_apks_container_installs(self):
        inspected=self.call('inspect-set',OUT/'runtime.apks');self.assertEqual(inspected['diagnostics']['dex_files'],2)
        app=self.install('runtime.apks');self.assertIn('MULTIDEX_OK',self.call('run',app['package'],'--headless')['output'])
    def test_split_missing_base_duplicate_and_mixed_package_rejected(self):
        for files in [('split-feature.apk',),('split-base.apk','split-feature.apk','split-feature.apk'),('split-base.apk','basic.apk')]:
            with self.subTest(files=files):self.call('install-set',*[OUT/f for f in files],ok=False)
        self.assertEqual(self.call('list')['apps'],[])
    def test_missing_feature_does_not_fake_execution(self):
        app=self.install('split-base.apk');r=self.call('run',app['package'],'--headless',ok=False);self.assertIn('Secondary',r.get('output','')+r.get('error',''))
    def test_split_integrity_is_checked_before_execution(self):
        app=self.install('runtime.apks');p=self.root/'packages'/app['package']/app['installation_id']/'splits/feature.code.apk';p.write_bytes(p.read_bytes()+b'tampered')
        r=self.call('run',app['package'],'--headless',ok=False);self.assertIn('integrity',r['error'])
    def test_unavailable_art_does_not_fall_back(self):
        backends=self.call('backends')['backends'];self.assertFalse(next(b for b in backends if b['id']=='aosp-art')['available'])
        app=self.install('basic.apk');r=self.call('run',app['package'],'--headless','--backend','aosp-art',ok=False);self.assertIn('unavailable',r['error'])
    def test_container_traversal_is_rejected(self):
        path=self.root/'bad.apks'
        with zipfile.ZipFile(path,'w') as z:z.writestr('../base.apk',(OUT/'split-base.apk').read_bytes())
        self.call('install',path,ok=False);self.assertEqual(self.call('list')['apps'],[])
    def test_real_ffmpeg_decode_and_invalid_media(self):
        video=self.root/'unprotected.mkv'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc=size=128x72:rate=1','-t','1','-c:v','ffv1',str(video)],check=True)
        info=self.call('media-probe',video);self.assertEqual(info['media']['streams'][0]['codec_name'],'ffv1')
        frame=self.call('media-decode',video);self.assertEqual(frame['decoded_frames'],1);self.assertEqual(len(frame['frame_sha256']),64);self.assertFalse(frame['protected_playback'])
        invalid=self.root/'bad.mkv';invalid.write_text('not media');self.call('media-decode',invalid,ok=False)
    def test_h264_hevc_vp9_av1_software_decode(self):
        for encoder,codec in [('libx264','h264'),('libx265','hevc'),('libvpx-vp9','vp9'),('libaom-av1','av1')]:
            with self.subTest(codec=codec):
                video=self.root/(codec+'.mkv')
                subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=64x64:rate=1','-frames:v','1','-c:v',encoder,'-threads','2',str(video)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
                frame=self.call('media-decode',video);self.assertEqual(frame['media']['streams'][0]['codec_name'],codec);self.assertEqual(frame['decoded_frames'],1)

if __name__=='__main__':unittest.main(verbosity=2)
