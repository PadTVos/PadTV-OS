import json,os,subprocess,tempfile,unittest
from pathlib import Path
from build_fixtures import ROOT,OUT
class Framework08Tests(unittest.TestCase):
    def test_original_private_trace_executes(self):
        self.run_fixture('trace08','ORIGINAL_PRIVATE_TRACE_WRITTEN_OK')
    def test_provider_initialization_order_typed_metadata_and_authority_isolation(self):
        self.run_fixture('providers08','ORIGINAL_PROVIDER_ORDER_METADATA_ALIAS_ISOLATION_OK')
    def test_build_metadata_identifies_linux_and_does_not_claim_certification(self):
        self.run_fixture('build08','PADBRIDGE_BUILD_IDENTITY_NO_DEVICE_ATTESTATION_OK')
    def test_original_aosp_tv_rating_roundtrip_and_domain_containment(self):
        self.run_fixture('rating08','ORIGINAL_AOSP_TV_RATING_ROUNDTRIP_CONTAINS_OK')
    def test_original_aosp_size_parsing_parcel_and_nonfinite_rejection(self):
        self.run_fixture('size08','ORIGINAL_AOSP_SIZE_PARSE_PARCEL_FINITE_OK')
    def test_original_parcelable_creator_preserves_binary_values(self):
        self.run_fixture('parcel08','ORIGINAL_PARCELABLE_CREATOR_ROUNDTRIP_OK')
    def test_xml_provider_preserves_utf8_and_rejects_entity_attacks(self):
        self.run_fixture('xml08','XML_UTF8_DTD_EXTERNAL_ENTITIES_REJECTED_OK')
    def run_fixture(self,name,marker):
        with tempfile.TemporaryDirectory() as folder:
            env={**os.environ,'PADBRIDGE_DATA_HOME':folder,'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
            def call(*args):
                p=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],capture_output=True,text=True,env=env,timeout=120)
                result=json.loads(p.stdout);self.assertTrue(result['ok'],result);return result
            app=call('install',OUT/(name+'.apk'))['app'];result=call('run',app['package'],'--headless');self.assertIn(marker,result['output'])
    def test_base_bundle_types_copy_and_missing_value_defaults(self):
        with tempfile.TemporaryDirectory() as folder:
            env={**os.environ,'PADBRIDGE_DATA_HOME':folder,'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
            def call(*args):
                p=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],capture_output=True,text=True,env=env,timeout=120)
                result=json.loads(p.stdout);self.assertTrue(result['ok'],result);return result
            app=call('install',OUT/'bundle08.apk')['app'];result=call('run',app['package'],'--headless');self.assertIn('ORIGINAL_BASEBUNDLE_TYPES_COPY_DEFAULTS_OK',result['output'])
    def test_original_key_listener_receives_both_edges_and_consumes_navigation(self):
        with tempfile.TemporaryDirectory() as folder:
            env={**os.environ,'PADBRIDGE_DATA_HOME':folder,'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
            def call(*args):
                p=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],capture_output=True,text=True,env=env,timeout=120)
                result=json.loads(p.stdout);self.assertTrue(result['ok'],result);return result
            app=call('install',OUT/'keys08.apk')['app'];(Path(folder)/'data'/app['package']/'test-keys.txt').write_text('22,23')
            result=call('run',app['package'],'--headless');self.assertIn('ORIGINAL_KEY_LISTENER_DOWN_UP_CONSUMPTION_OK',result['output'])
    def test_original_context_menu_scene_and_dpad_callback(self):
        with tempfile.TemporaryDirectory() as folder:
            env={**os.environ,'PADBRIDGE_DATA_HOME':folder,'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
            def call(*args):
                p=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],capture_output=True,text=True,env=env,timeout=120)
                result=json.loads(p.stdout);self.assertTrue(result['ok'],result);return result
            app=call('install',OUT/'menu08.apk')['app'];data=Path(folder)/'data'/app['package'];(data/'test-keys.txt').write_text('82')
            opened=call('run',app['package'],'--headless');scene=json.loads(opened['output'].split('PADBRIDGE_SCENE=')[1].splitlines()[0]);panel=scene['nodes'][scene['root']]
            self.assertEqual([scene['nodes'][i]['text'] for i in panel['children']],['Playback options','Dismiss','Play clip'])
            (data/'test-keys.txt').write_text('82,20,23');selected=call('run',app['package'],'--headless')
            self.assertIn('ORIGINAL_CONTEXT_MENU_CLOSED',selected['output']);self.assertEqual((data/'files/selected.txt').read_text(),'ORIGINAL_MENU_CALLBACK_20')
    def test_scroll_bounds_canvas_pixels_and_window_lifecycle(self):
        with tempfile.TemporaryDirectory() as folder:
            env={**os.environ,'PADBRIDGE_DATA_HOME':folder,'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
            def call(*args):
                p=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],capture_output=True,text=True,env=env,timeout=120)
                result=json.loads(p.stdout);self.assertTrue(result['ok'],result);return result
            app=call('install',OUT/'scroll08.apk')['app'];result=call('run',app['package'],'--headless')
            self.assertIn('SCROLL_GEOMETRY_CANVAS_WINDOW_LIFECYCLE_OK',result['output'])
            from PIL import Image
            frames=[Image.open(p).convert('RGBA') for p in (Path(folder)/'data'/app['package']).glob('rendered-view-*.png')]
            self.assertTrue(any(im.size==(80,50) and im.getpixel((12,12))==(0,255,0,255) and im.getpixel((32,12))==(16,16,16,255) for im in frames))
    def test_original_compiled_styles_theme_inheritance_and_typed_array(self):
        with tempfile.TemporaryDirectory() as folder:
            env={**os.environ,'PADBRIDGE_DATA_HOME':folder,'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
            def call(*args):
                p=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],capture_output=True,text=True,env=env,timeout=120)
                result=json.loads(p.stdout);self.assertTrue(result['ok'],result);return result
            app=call('install',OUT/'theme08.apk')['app'];result=call('run',app['package'],'--headless')
            self.assertIn('ORIGINAL_STYLE_THEME_TYPED_ARRAY_OK',result['output'])
            trace=json.loads(Path(result['startup_trace']).read_text());self.assertEqual(trace['status'],'exited_successfully')
            self.assertEqual(trace['package_identity']['sha256'],app['sha256']);self.assertEqual(trace['process_exit_code'],0);self.assertFalse(trace['application_reported']['trusted'])
            self.assertEqual([s['stage'] for s in trace['stages']],['backend.select','package.integrity','dex.inspect','native.stage','dex.prepare','sandbox.prepare','sandbox.execute','process.exit'])
    def test_startup_trace_preserves_exact_backend_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            env={**os.environ,'PADBRIDGE_DATA_HOME':folder,'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
            p=subprocess.run([str(ROOT/'target/release/padbridge'),'run','org.padtv.absent','--backend','unknown'],capture_output=True,text=True,env=env,timeout=10)
            result=json.loads(p.stdout);self.assertFalse(result['ok'])
            trace=json.loads((Path(folder)/'logs/org.padtv.absent.startup.json').read_text());self.assertEqual(trace['status'],'failed');self.assertIn('Unknown runtime backend',trace['error'])
            self.assertEqual(trace['stages'][0]['stage'],'backend.select')
    def test_layout_observer_real_bounds_margins_and_cancelled_predraw(self):
        with tempfile.TemporaryDirectory() as folder:
            env={**os.environ,'PADBRIDGE_DATA_HOME':folder,'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
            def call(*args):
                p=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],capture_output=True,text=True,env=env,timeout=120)
                result=json.loads(p.stdout);self.assertTrue(result['ok'],result);return result
            app=call('install',OUT/'layout08.apk')['app'];result=call('run',app['package'],'--headless')
            self.assertIn('REAL_LAYOUT_EVENTS_MARGINS_PREDRAW_OK',result['output'])
            self.assertIn('PADBRIDGE_PHASE=window.draw',result['output'])
            from PIL import Image
            frames=list((Path(folder)/'data'/app['package']).glob('rendered-view-*.png'))
            self.assertTrue(frames)
            self.assertTrue(any(Image.open(p).convert('RGBA').getpixel((20,20))==(10,200,30,255) for p in frames))
if __name__=='__main__':unittest.main(verbosity=2)
