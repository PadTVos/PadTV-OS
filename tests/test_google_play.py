import subprocess
import unittest
from dataclasses import replace
from unittest.mock import patch

from padtv import android
from padtv_store.catalog import load, validate
from padtv_store.providers import GooglePlayProvider


class GooglePlayTests(unittest.TestCase):
    def setUp(self):
        self.youtube = next(p for p in load() if p.id == 'youtube-tv')

    def test_tv_catalog_uses_official_packages_and_removes_old_defaults(self):
        products = {p.id: p for p in load()}
        self.assertNotIn('system-kodi', products)
        self.assertNotIn('jellyfin-desktop', products)
        self.assertEqual(products['youtube-tv'].target, 'com.google.android.youtube.tv')
        self.assertEqual(products['netflix-tv'].target, 'com.netflix.ninja')
        self.assertEqual(products['youtube-tv'].source, 'google-play')

    def test_android_catalog_rejects_urls_commands_and_other_sources(self):
        for change in ({'target':'https://mirror.test/app.apk'}, {'target':'com.foo;reboot'},
                       {'target':'--option'}, {'source':'web'}, {'kind':'web'}):
            with self.assertRaises(ValueError): validate(replace(self.youtube, **change))

    def test_provider_open_is_not_reported_as_completed_install(self):
        with patch('padtv_store.providers.run', return_value='{"ok":true,"opened":true,"installed":false}') as run:
            result = GooglePlayProvider().install(self.youtube)
        self.assertTrue(result['opened'])
        self.assertFalse(result['installed'])
        self.assertEqual(run.call_args.args[0], ['padtv-android','play','com.google.android.youtube.tv'])

    def test_provider_rejects_error_reply(self):
        with patch('padtv_store.providers.run', return_value='{"ok":false,"error":"Google Play missing"}'):
            with self.assertRaisesRegex(RuntimeError, 'Google Play missing'):
                GooglePlayProvider().install(self.youtube)

    def test_play_package_validation_happens_before_starting_android(self):
        with patch.object(android, 'ensure_session') as start:
            with self.assertRaises(android.AndroidError): android.execute('play','com.foo&bad=true')
            start.assert_not_called()

    def test_play_requires_official_store_client(self):
        with patch.object(android,'ensure_session'), patch.object(android,'app_list',return_value=[]), patch.object(android,'run') as run:
            with self.assertRaisesRegex(android.AndroidError,'Google Play'):
                android.execute('play',self.youtube.target)
            run.assert_not_called()

    def test_play_opens_market_page_without_installer_or_fake_success(self):
        with patch.object(android,'ensure_session'), patch.object(android,'app_list',return_value=[{'package':'com.android.vending'}]), patch.object(android,'run') as run:
            reply = android.execute('play',self.youtube.target)
        self.assertFalse(reply['installed'])
        self.assertEqual(run.call_args_list[0].args[0], ['waydroid','app','intent','android.intent.action.VIEW','market://details?id=com.google.android.youtube.tv'])
        self.assertFalse(any('install' in call.args[0] for call in run.call_args_list))

    def test_inventory_does_not_start_stopped_android(self):
        with patch.object(android,'status',return_value={'running':False,'initialized':True,'google_play':True}), patch.object(android,'run') as run:
            result=android.inventory()
            self.assertFalse(result['known'])
            run.assert_not_called()

    def test_inventory_only_reports_ready_installed_packages(self):
        with patch.object(android,'status',return_value={'running':True,'initialized':True,'google_play':True}), patch.object(android,'run',return_value=subprocess.CompletedProcess([],0,'1\n','')), patch.object(android,'app_list',return_value=[{'package':'com.netflix.ninja'}]):
            result=android.inventory()
            self.assertTrue(result['known'])
            self.assertEqual(result['packages'],['com.netflix.ninja'])

    def test_prepare_does_not_downgrade_existing_google_play(self):
        state={'initialized':True,'google_play':True}
        with patch.object(android.sys,'platform','linux'), patch.object(android,'status',return_value=state), patch.object(android,'run') as run:
            self.assertEqual(android.execute('prepare'),state)
            run.assert_not_called()
