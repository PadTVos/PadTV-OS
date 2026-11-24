import json
from pathlib import Path
import tempfile
import unittest
from padtv.apps import AppLibrary,UserApp
from padtv.padbridge_ui import bridge_app
from padtv.session import app_id

class PadBridgeIntegrationTests(unittest.TestCase):
    def test_manifest_and_launch_preserve_other_runtimes(self):
        with tempfile.TemporaryDirectory() as folder:
            library=AppLibrary(folder)
            bridge=UserApp('padbridge.org.example.app','Example','padbridge','org.example.app')
            legacy=UserApp('android.org.example.app','Legacy','android','org.example.app')
            library.install(bridge);library.install(legacy)
            self.assertEqual(library.command(bridge),('padbridge','run','org.example.app','--restart-once'))
            self.assertEqual(library.command(legacy),('padtv-android','launch','org.example.app'))
            library.remove(bridge);self.assertIn(legacy,library.list())
    def test_metadata_paths_and_wayland_identity(self):
        app=bridge_app({'package':'org.example.app','sha256':'a'*64,'title':'Example','icon':'res/icon.png'})
        self.assertEqual(app_id('user:'+app.id,['padbridge','run',app.target,'--restart-once']),'padbridge.org.example.app')
        self.assertTrue(app.icon_path.endswith('icon'))
        for package,digest in [('../bad','a'*64),('org.example.app','../bad')]:
            with self.assertRaises(ValueError):bridge_app({'package':package,'sha256':digest,'title':'bad','icon':'x'})
    def test_catalog_official_sources_remain_distinct(self):
        catalog=json.loads((Path(__file__).resolve().parents[1]/'catalog/apps.json').read_text(encoding='utf-8'))
        products=catalog['apps']
        for package in ('com.google.android.youtube.tv','com.netflix.ninja'):
            self.assertEqual(next(p for p in products if p['target']==package)['source'],'google-play')
