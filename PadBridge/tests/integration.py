"""Real signed APKs and mandatory bubblewrap. Requires Linux, never skips isolation."""
import hashlib, http.server, json, os, subprocess, tempfile, threading, unittest, zipfile
from pathlib import Path
from build_fixtures import build, ROOT

class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.fixtures=build()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='padbridge-tests-')
        self.data=Path(self.temp.name)
        self.env={**os.environ,'PADBRIDGE_DATA_HOME':str(self.data),'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
    def tearDown(self):self.temp.cleanup()
    def call(self,*args,ok=True):
        result=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],env=self.env,capture_output=True,text=True,timeout=120)
        try:value=json.loads(result.stdout)
        except ValueError:self.fail(result.stdout+result.stderr)
        self.assertEqual(value['ok'],ok,value)
        return value
    def install(self,name='basic'):return self.call('install',self.fixtures/(name+'.apk'))['app']
    def test_signature_and_original_bytes(self):
        app=self.install();stored=self.data/'packages'/app['package']/app['sha256']/'original.apk'
        self.assertEqual(stored.read_bytes(),(self.fixtures/'basic.apk').read_bytes());self.assertEqual(len(app['signers']),1)
        self.assertTrue(app['icon']);self.assertTrue(app['television'])
    def test_tamper_rejected(self):
        path=self.data/'tampered.apk';path.write_bytes((self.fixtures/'basic.apk').read_bytes())
        with zipfile.ZipFile(path,'a') as apk:apk.writestr('assets/changed.txt','tamper')
        self.call('install',path,ok=False);self.assertEqual(self.call('list')['apps'],[])
    def test_wrong_signer_downgrade_and_data_preservation(self):
        app=self.install();data=self.data/'data'/app['package'];(data/'keep').write_text('saved')
        self.call('install',self.fixtures/'wrong-signer.apk',ok=False)
        self.install('update');self.call('install',self.fixtures/'basic.apk',ok=False)
        self.assertEqual((data/'keep').read_text(),'saved')
    def test_remove_data_is_explicit(self):
        app=self.install();data=self.data/'data'/app['package'];(data/'keep').write_text('saved')
        self.call('remove',app['package']);self.assertTrue((data/'keep').exists());self.assertEqual(self.call('list')['apps'],[])
        self.install();self.call('remove',app['package'],'--delete-data');self.assertFalse(data.exists())
    def test_dex_activity_image_storage_and_dpad(self):
        app=self.install();data=self.data/'data'/app['package'];(data/'test-keys.txt').write_text('20,23')
        result=self.call('run',app['package'],'--headless')
        self.assertIn('DEX_ACTIVITY_STORAGE_OK',result['output']);self.assertIn('DPAD_CLICK_OK',result['output'])
        self.assertEqual((data/'files/result.txt').read_text(),'42')
        scene=json.loads(result['output'].split('PADBRIDGE_SCENE=')[1].splitlines()[0])
        self.assertTrue(any(n['image_bytes']>100 for n in scene['nodes']))
    def test_network_permission_is_enforced(self):
        app=self.install('network');files=self.data/'data'/app['package']/'files';files.mkdir()
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):self.send_response(200);self.end_headers();self.wfile.write(b'NETWORK_OK\n')
            def log_message(self,*args):pass
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            (files/'url.txt').write_text(f'http://127.0.0.1:{server.server_port}/\n')
            self.call('run',app['package'],'--headless',ok=False)
            self.call('permissions',app['package'],'["android.permission.INTERNET"]')
            result=self.call('run',app['package'],'--headless');self.assertIn('NETWORK_OK',result['output'])
        finally:server.shutdown();server.server_close();thread.join()
    def test_host_path_isolation(self):
        secret=Path('/tmp/padbridge-host-secret');secret.write_text('private-test-value')
        try:
            app=self.install('isolation');result=self.call('run',app['package'],'--headless')
            self.assertIn('HOST_PATHS_HIDDEN_OK',result['output'])
        finally:secret.unlink()
    def test_bounded_crash_recovery(self):
        app=self.install('crash');result=self.call('run',app['package'],'--headless','--restart-once')
        self.assertEqual(result['attempts'],2);self.assertIn('CRASH_RECOVERY_OK',result['output'])
    def test_audio_video_report_unsupported(self):
        for name,api in [('audio','android.media.AudioTrack'),('media','android.media.MediaCodec')]:
            with self.subTest(name=name):
                result=self.call('diagnose',self.fixtures/(name+'.apk'));self.assertIn(api,result['diagnostics']['unsupported_classes'])
                app=self.install(name);self.call('run',app['package'],'--headless',ok=False)
    def test_archive_paths_rejected(self):
        for name in ['../escape','/absolute','assets/../../escape']:
            with self.subTest(name=name):
                path=self.data/'invalid.apk'
                with zipfile.ZipFile(path,'w') as z:
                    z.writestr('AndroidManifest.xml',b'x');z.writestr('classes.dex',b'x');z.writestr(name,b'x')
                self.call('inspect',path,ok=False)
    def test_native_elf_dependencies_are_reported_and_rejected(self):
        result=self.call('diagnose',self.fixtures/'native.apk')
        library=result['diagnostics']['native_details'][0]
        self.assertEqual(library['elf_machine'],62)
        self.assertIn('libc.so.6',library['needed'])
        app=self.install('native');self.call('run',app['package'],'--headless',ok=False)
    def test_leanback_only_launcher(self):
        app=self.install('tvonly');self.assertTrue(app['television']);self.assertEqual(app['activity'],'org.padtv.fixture.Main')
        self.assertIn('DEX_ACTIVITY_STORAGE_OK',self.call('run',app['package'],'--headless')['output'])
    def test_integrity_and_unrequested_permission(self):
        app=self.install();self.call('permissions',app['package'],'["android.permission.INTERNET"]',ok=False)
        apk=self.data/'packages'/app['package']/app['sha256']/'original.apk';apk.write_bytes(b'corrupt')
        self.call('run',app['package'],'--headless',ok=False)
    def test_damaged_metadata_cannot_replace_signer(self):
        app=self.install();(self.data/'packages'/app['package']/'current.json').write_text('{')
        result=self.call('install',self.fixtures/'wrong-signer.apk',ok=False)
        self.assertIn('metadata is damaged',result['error'])

if __name__=='__main__':unittest.main(verbosity=2)
