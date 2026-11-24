import json
from pathlib import Path
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch
from padtv_store.catalog import load, validate
from padtv_store.providers import FlatpakProvider
from padtv.apps import AppLibrary, UserApp

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.products = load()
        self.native = next(p for p in self.products if p.id == 'vlc')

    def test_catalog_rejects_command_and_url_injection(self):
        for target in ('--system', 'org.valid.App; reboot', '../app', 'https://evil.test/a'):
            with self.assertRaises(ValueError):
                validate(replace(self.native, target=target))
        youtube = next(p for p in self.products if p.id=='youtube')
        for url in ('file:///etc/passwd', 'javascript:alert(1)', 'https://user:pass@host.test', 'http://host.test'):
            with self.assertRaises(ValueError):
                validate(replace(youtube,target=url))

    def test_duplicate_catalog_id_rejected(self):
        from dataclasses import asdict
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'catalog.json'
            path.write_text(json.dumps({'schema_version':1,'apps':[asdict(self.native)]*2}))
            with self.assertRaises(ValueError): load(path)

    def test_install_is_user_scoped_and_verified_before_success(self):
        with patch('padtv_store.providers.run',side_effect=['','flathub\thttps://dl.flathub.org/repo/\n','',self.native.target+'\n']) as run:
            FlatpakProvider().install(self.native)
        for call in run.call_args_list:
            self.assertIn('--user',call.args[0])
            self.assertNotIn('--system',call.args[0])
        with patch('padtv_store.providers.run',side_effect=['','flathub\thttps://dl.flathub.org/repo/\n','','']):
            with self.assertRaises(RuntimeError): FlatpakProvider().install(self.native)

    def test_conflicting_flathub_remote_is_rejected(self):
        with patch('padtv_store.providers.run',side_effect=['','flathub\thttps://untrusted.test/\n']) as run:
            with self.assertRaises(RuntimeError): FlatpakProvider().install(self.native)
        self.assertEqual(run.call_count,2)

    def test_community_packages_cannot_execute_without_configured_trust(self):
        product=replace(self.native,source='padtv')
        self.assertFalse(product.installable)
        with patch('padtv_store.providers.run') as run:
            with self.assertRaises(ValueError): FlatpakProvider().install(product)
            run.assert_not_called()

    def test_flatpak_library_uses_fixed_argv(self):
        app=UserApp('vlc','VLC','flatpak','org.videolan.VLC')
        with tempfile.TemporaryDirectory() as folder:
            library=AppLibrary(folder)
            library.install(app)
            self.assertIn(app,library.list())
            self.assertEqual(library.command(app),('flatpak','run','org.videolan.VLC'))

    def test_apt_cannot_be_removed_through_user_provider(self):
        product=next(p for p in self.products if p.kind=='apt')
        self.assertFalse(product.installable)
        with patch('padtv_store.providers.run') as run:
            with self.assertRaises(ValueError): FlatpakProvider().remove(product)
            run.assert_not_called()

    def test_running_native_app_cannot_be_removed(self):
        with patch('padtv_store.providers.run',return_value=self.native.target+'\n') as run:
            with self.assertRaisesRegex(RuntimeError,'zavřete'):
                FlatpakProvider().remove(self.native)
        self.assertEqual(run.call_count,1)
