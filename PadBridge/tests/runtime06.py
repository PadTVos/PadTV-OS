"""Native execution, APKM and analyzer integration under mandatory bubblewrap."""
import json, os, subprocess, tempfile, unittest, zipfile
from pathlib import Path
from build_fixtures import ROOT, OUT

class NativeCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='padbridge06-');self.root=Path(self.temp.name)
        self.env={**os.environ,'PADBRIDGE_DATA_HOME':str(self.root),'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
    def tearDown(self):self.temp.cleanup()
    def call(self,*args,ok=True):
        p=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],env=self.env,capture_output=True,text=True,timeout=150)
        try:r=json.loads(p.stdout)
        except ValueError:self.fail(p.stdout+p.stderr)
        self.assertEqual(r['ok'],ok,r);return r
    def test_original_native_android_elf_jni_and_syscall_sandbox(self):
        secret=Path('/tmp/padbridge-native-host-secret');secret.write_text('host private')
        try:
            meta=self.call('inspect',OUT/'native-jni.apk');self.assertTrue(meta['diagnostics']['native_abi_supported'])
            self.assertEqual(meta['diagnostics']['native_details'][0]['needed'],[])
            app=self.call('install',OUT/'native-jni.apk')['app']
            result=self.call('run',app['package'],'--headless')
            self.assertIn('ORIGINAL_DEX_NATIVE_X86_64_JNI_OK',result['output'])
            self.assertIn('NATIVE_HOST_PATHS_HIDDEN_OK',result['output'])
            self.assertEqual(secret.read_text(),'host private')
        finally:secret.unlink()
    def test_apkm_signed_split_execution(self):
        path=self.root/'bundle.apkm';path.write_bytes((OUT/'runtime.apks').read_bytes())
        app=self.call('install',path)['app'];self.assertEqual(len(app['splits']),1)
        self.assertIn('MULTIDEX_OK',self.call('run',app['package'],'--headless')['output'])
    def test_analyzer_native_dependencies_and_html(self):
        html=self.root/'report.html';r=self.call('analyze',OUT/'native.apk','--html',html)
        self.assertIn('libc.so.6',r['native']['native_details'][0]['needed'])
        self.assertFalse(r['native']['native_abi_supported']);self.assertIn('Static references',html.read_text())
        self.assertEqual(r['observed_runtime_errors'],[])
    def test_analyzer_static_classes_and_observed_failure_are_separate(self):
        app=self.call('install',OUT/'audio.apk')['app']
        self.call('run',app['package'],'--headless',ok=False)
        r=self.call('analyze',OUT/'audio.apk')
        # AudioTrack is implemented in 0.4; this original APK still requests an
        # unimplemented native device query. Preserve the diagnostic regression.
        self.assertNotIn('android/media/AudioTrack',r['static']['missing_classes'])
        self.assertTrue(any('AudioTrack.getNativeOutputSampleRate(I)I' in m for m in r['static']['missing_methods']))
        self.assertTrue(r['observed_runtime_errors']);self.assertTrue(r['runtime_log_matches_installed_build'])
    def test_analyzer_multidex_and_no_false_missing_app_classes(self):
        r=self.call('analyze',OUT/'java-multidex.apk')
        self.assertEqual(r['static']['dex_files'],2);self.assertEqual(r['static']['analysis_errors'],[])
        self.assertNotIn('org/padtv/runtimeprobe/Secondary',r['static']['missing_classes'])
    def test_analyzer_exact_signature_in_dormant_code(self):
        r=self.call('analyze',OUT/'native-jni.apk')
        self.assertTrue(any(m.endswith('.getPreferences(I)Landroid/content/SharedPreferences;') for m in r['static']['missing_methods']),r)
        self.assertEqual(r['observed_runtime_errors'],[])
    def test_old_runtime_log_not_attributed_to_updated_apk(self):
        app=self.call('install',OUT/'basic.apk')['app']
        self.call('run',app['package'],'--headless')
        self.assertTrue(self.call('analyze',OUT/'basic.apk')['runtime_log_matches_installed_build'])
        self.call('install',OUT/'update.apk')
        report=self.call('analyze',OUT/'update.apk')
        self.assertFalse(report['runtime_log_matches_installed_build'])
        self.assertEqual(report['observed_runtime_errors'],[])

if __name__=='__main__':unittest.main(verbosity=2)
