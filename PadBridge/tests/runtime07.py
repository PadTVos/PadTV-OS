"""0.4 native ABI and original exception-handler regression tests."""
import hashlib,json,os,subprocess,tempfile,unittest
from pathlib import Path
from build_fixtures import ROOT,OUT

class Runtime07Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='runtime07-');self.root=Path(self.temp.name)
        self.env={**os.environ,'PADBRIDGE_DATA_HOME':str(self.root),'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
    def tearDown(self):self.temp.cleanup()
    def call(self,*args):
        p=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],env=self.env,text=True,capture_output=True,timeout=150);r=json.loads(p.stdout);self.assertTrue(r['ok'],r);return r
    def test_original_android_elf_registers_jni_and_executes_memory_abi(self):
        path=OUT/'abi07.apk';meta=self.call('inspect',path);native=meta['diagnostics']['native_details'][0]
        self.assertTrue(native['supported']);self.assertEqual(native['needed'],['libc.so']);self.assertIn('malloc',native['undefined_symbols'])
        app=self.call('install',path)['app'];result=self.call('run',app['package'],'--headless');self.assertIn('JNI_REGISTER_MEMORY_ABI_OK',result['output'])
        original=self.root/'packages'/app['package']/app['sha256']/'original.apk';self.assertEqual(hashlib.sha256(original.read_bytes()).digest(),hashlib.sha256(path.read_bytes()).digest())
    def test_unsupported_library_cannot_load_even_when_java_can_start(self):
        path=OUT/'reject07.apk';self.assertFalse(self.call('inspect',path)['diagnostics']['native_abi_supported'])
        app=self.call('install',path)['app'];self.assertIn('UNSUPPORTED_NATIVE_LOAD_REJECTED',self.call('run',app['package'],'--headless')['output'])
    def test_original_dex_catch_target_zero_preserves_exception_retry(self):
        app=self.call('install',OUT/'zero07.apk')['app'];self.assertIn('DEX_ZERO_HANDLER_OK',self.call('run',app['package'],'--headless')['output'])
    def test_dex_elided_constructor_preserves_class_arguments_and_side_effects(self):
        app=self.call('install',OUT/'ctors07.apk')['app'];self.assertIn('DEX_CONSTRUCTOR_CLASS_ARGUMENT_SIDE_EFFECT_OK',self.call('run',app['package'],'--headless')['output'])
    def test_original_gles_shaders_produce_real_triangle_pixels(self):
        app=self.call('install',OUT/'gl07.apk')['app'];self.assertIn('REAL_EGL_GLES_SHADER_OK',self.call('run',app['package'],'--headless')['output'])
        pixels=(self.root/'data'/app['package']/'files/triangle.rgba').read_bytes();self.assertEqual(len(pixels),64*64*4)
        def pixel(x,y):return tuple(pixels[(y*64+x)*4:(y*64+x+1)*4])
        self.assertEqual(pixel(32,32),(255,0,0,255));self.assertEqual(pixel(0,0),(0,0,255,255))
    def test_original_application_context_and_full_activity_callback_order(self):
        app=self.call('install',OUT/'lifecycle07.apk')['app'];r=self.call('run',app['package'],'--headless')
        self.assertIn('APPLICATION_CONTEXT_BASE64_OK',r['output'])
        lines=[line for line in r['output'].splitlines() if line.startswith('APP_LIFECYCLE_')]
        self.assertEqual(lines,['APP_LIFECYCLE_'+s for s in ['CREATED','STARTED','RESUMED','PAUSED','STOPPED','DESTROYED']])

if __name__=='__main__':unittest.main(verbosity=2)
