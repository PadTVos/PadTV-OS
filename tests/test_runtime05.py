import json
from pathlib import Path
import unittest
from padtv.padbridge_ui import bridge_app
from padtv_store.catalog import load

class Runtime05IntegrationTests(unittest.TestCase):
    def test_split_installation_identity_is_used_for_icon(self):
        metadata={'package':'org.example.split','title':'Split','sha256':'a'*64,'installation_id':'b'*64,'icon':'res/icon.png'}
        self.assertIn('b'*64,bridge_app(metadata).icon_path)
        metadata['installation_id']='../outside'
        with self.assertRaises(ValueError):bridge_app(metadata)
    def test_android_catalog_exposes_unverified_compatibility(self):
        apps=[p for p in load() if p.kind=='android']
        self.assertGreaterEqual(len(apps),2)
        for app in apps:
            # 0.7 has observed launch failures, rather than only untested APKs.
            # Keep the original safety check: never advertise them as working.
            self.assertEqual(app.compatibility_status,'unsupported')
            self.assertIn('nefunguje',app.compatibility.lower())

if __name__=='__main__':unittest.main()
