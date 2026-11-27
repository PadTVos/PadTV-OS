from dataclasses import replace
import json,tempfile,unittest
from pathlib import Path
from padtv.apps import AppLibrary,UserApp

class Runtime08Tests(unittest.TestCase):
    def test_legacy_manifest_defaults_and_refresh_preserves_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            library=AppLibrary(folder);app=UserApp('padbridge.org.test.app','Original','padbridge','org.test.app')
            library.install(app);path=Path(folder)/'apps'/f'{app.id}.json'
            old=json.loads(path.read_text());old.pop('runtime_backend');path.write_text(json.dumps(old))
            self.assertEqual(next(a for a in library.list() if a.id==app.id).runtime_backend,'')
            library.install(replace(app,runtime_backend='aosp-art'));library.install(replace(app,title='Updated'))
            updated=next(a for a in library.list() if a.id==app.id)
            self.assertEqual(updated.runtime_backend,'aosp-art');self.assertEqual(updated.title,'Updated')
            self.assertEqual(library.command(updated)[-2:],('--backend','aosp-art'))
            library.install(replace(app,runtime_backend='enjarify-openjdk'))
            self.assertEqual(next(a for a in library.list() if a.id==app.id).runtime_backend,'enjarify-openjdk')
    def test_runtime_cannot_inject_command_or_change_web_application(self):
        with tempfile.TemporaryDirectory() as folder:
            library=AppLibrary(folder)
            for app in [UserApp('test','Test','padbridge','org.test.app',runtime_backend='art; reboot'),UserApp('test','Test','web','https://example.com',runtime_backend='aosp-art')]:
                with self.assertRaises(ValueError):library.install(app)
if __name__=='__main__':unittest.main()
