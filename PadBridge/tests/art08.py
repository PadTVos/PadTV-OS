"""Original signed APK on the installed ART backend, never an Android emulator."""
import hashlib, json, os, subprocess, tempfile, unittest
from pathlib import Path
from build_fixtures import ROOT,OUT

class Art08Tests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.data=Path(self.folder.name)
        self.env={**os.environ,'PADBRIDGE_DATA_HOME':str(self.data),'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
        backends=self.call('backends')['backends']
        art=next(b for b in backends if b['id']=='aosp-art')
        if not art['available']:self.skipTest('Install the pinned ART bundle using padbridge setup-art')
        self.art=Path(art['root'])
    def call(self,*args,ok=True):
        p=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],capture_output=True,text=True,env=self.env,timeout=120)
        result=json.loads(p.stdout)
        if ok:self.assertTrue(result['ok'],result)
        return result
    def install(self):return self.call('install',OUT/'art08.apk')['app']
    def test_original_trace_records_real_monotonic_events(self):
        app=self.call('install',OUT/'trace08.apk')['app'];result=self.call('run',app['package'],'--backend','aosp-art','--headless')
        self.assertIn('ORIGINAL_PRIVATE_TRACE_WRITTEN_OK',result['output'])
        events=[json.loads(s) for s in (self.data/'data'/app['package']/'trace.jsonl').read_text().splitlines()]
        self.assertEqual([e['phase'] for e in events],['B','C','E','S','F']);self.assertEqual(events[1]['value'],42)
        self.assertGreater(events[2]['monotonic_ns'],events[0]['monotonic_ns'])
        self.assertEqual(events[3]['value'],events[4]['value'])
    def test_provider_startup_order_metadata_and_failed_initialization(self):
        app=self.call('install',OUT/'providers08.apk')['app']
        self.assertIn('ORIGINAL_PROVIDER_ORDER_METADATA_ALIAS_ISOLATION_OK',self.call('run',app['package'],'--backend','aosp-art','--headless')['output'])
        app=self.call('install',OUT/'provider-fails08.apk')['app']
        result=self.call('run',app['package'],'--backend','aosp-art','--headless',ok=False)
        self.assertFalse(result['ok']);self.assertIn('PADBRIDGE_FAILED_PHASE=providers.initialize',result['output'])
    def test_original_kotlin_dex_and_input(self):
        app=self.call('install',OUT/'kotlin.apk')['app'];(self.data/'data'/app['package']/'test-keys.txt').write_text('23')
        result=self.call('run',app['package'],'--backend','aosp-art','--headless')
        self.assertIn('KOTLIN_ORIGINAL_DEX_OK',result['output']);self.assertIn('KOTLIN_DPAD_OK',result['output'])
    def test_original_multidex_and_split_feature_execution(self):
        app=self.call('install',OUT/'art-multidex.apk')['app']
        self.assertIn('ORIGINAL_ART_FEATURE_DEX_42',self.call('run',app['package'],'--backend','aosp-art','--headless')['output'])
        app=self.call('install-set',OUT/'art-split-feature.apk',OUT/'art-split-base.apk')['app']
        folder=self.data/'packages'/app['package']/app['installation_id']
        self.assertEqual((folder/'original.apk').read_bytes(),(OUT/'art-split-base.apk').read_bytes())
        self.assertEqual((folder/'splits/feature.code.apk').read_bytes(),(OUT/'art-split-feature.apk').read_bytes())
        self.assertIn('ORIGINAL_ART_FEATURE_DEX_42',self.call('run',app['package'],'--backend','aosp-art','--headless')['output'])
    def test_missing_feature_is_a_real_failure(self):
        app=self.call('install',OUT/'art-split-base.apk')['app']
        result=self.call('run',app['package'],'--backend','aosp-art','--headless',ok=False)
        self.assertFalse(result['ok']);self.assertIn('Secondary',result['output'])
    def test_original_apk_dex_reflection_threads_exceptions_and_private_data(self):
        original=(OUT/'art08.apk').read_bytes();app=self.install()
        result=self.call('run',app['package'],'--backend','aosp-art','--headless')
        self.assertEqual(app['sha256'],hashlib.sha256(original).hexdigest())
        self.assertEqual((OUT/'art08.apk').read_bytes(),original)
        self.assertIn('ART_ORIGINAL_DEX_REFLECTION_THREADS_EXCEPTIONS_OK 40000',result['output'])
        self.assertIn('ORIGINAL_ART_MAIN_LOOPER_CALLBACK',result['output'])
        self.assertTrue((self.data/'data'/app['package']/'art-result.txt').is_file())
        trace=json.loads(Path(result['startup_trace']).read_text());self.assertEqual(trace['status'],'exited_successfully');self.assertEqual(trace['backend'],'aosp-art')
        self.assertFalse(list((self.data/'apps').rglob('classes.jar')),'ART must not translate the APK to JVM bytecode')
    def test_original_activity_scene_and_dpad_callback(self):
        app=self.install();data=self.data/'data'/app['package'];(data/'test-keys.txt').write_text('20,23')
        result=self.call('run',app['package'],'--backend','aosp-art','--headless')
        self.assertEqual((data/'files/input.txt').read_text(),'ORIGINAL_ART_DPAD_CLICK')
        scene=json.loads(result['output'].split('PADBRIDGE_SCENE=')[1].splitlines()[0])
        self.assertIn('ORIGINAL_ART_DPAD_CLICK',[n['text'] for n in scene['nodes']])
    def test_original_parcel_and_aosp_size_on_libcore(self):
        app=self.call('install',OUT/'size08.apk')['app']
        result=self.call('run',app['package'],'--backend','aosp-art','--headless')
        self.assertIn('ORIGINAL_AOSP_SIZE_PARSE_PARCEL_FINITE_OK',result['output'])
    def test_original_aosp_tv_rating_on_libcore(self):
        app=self.call('install',OUT/'rating08.apk')['app']
        result=self.call('run',app['package'],'--backend','aosp-art','--headless')
        self.assertIn('ORIGINAL_AOSP_TV_RATING_ROUNDTRIP_CONTAINS_OK',result['output'])
    def test_real_jni_activation_boot_image_and_source_integrity(self):
        import sys
        sys.path.insert(0,str(ROOT/'runtime'));import art_runtime
        proof=art_runtime.verify(self.art)
        self.assertEqual(proof['jni_create_result'],0)
        self.assertTrue(proof['original_dex_executed'])
        self.assertIn('boot/x86_64/boot.art',proof['files'])
        self.assertIn('"original_main_completed":true',proof['probe']['stdout'])
    def test_tampered_runtime_is_rejected_before_apk_execution(self):
        # A minimal independent damaged installation, never modify the active runtime.
        import sys
        sys.path.insert(0,str(ROOT/'runtime'));import art_runtime
        with tempfile.TemporaryDirectory() as folder:
            fake=Path(folder);proof=json.loads((self.art/'padbridge-art.json').read_text());(fake/'padbridge-art.json').write_text(json.dumps(proof))
            with self.assertRaisesRegex(ValueError,'integrity mismatch'):art_runtime.verify(fake)
if __name__=='__main__':unittest.main(verbosity=2)
