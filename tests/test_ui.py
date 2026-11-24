import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from padtv.ui import ChoiceDialog, HomeWindow
from padtv.apps import YOUTUBE, UserApp


class UITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.app_data = tempfile.TemporaryDirectory()
        self.window = HomeWindow(preview=True, apps_dir=self.app_data.name)
        self.window.resize(1600, 900)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.app_data.cleanup()

    def test_remote_navigation_and_back(self):
        self.window.set_page("apps")
        self.app.processEvents()
        self.assertEqual(self.app.focusWidget().text(), "YouTube")
        QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Right)
        self.assertEqual(self.app.focusWidget().text(), "Prohlížeč")
        QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Enter)
        self.assertIn("Náhled", self.window.notice)
        QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Escape)
        self.assertEqual(self.window.page, "home")

    def test_preview_never_starts_a_process(self):
        with patch("padtv.ui.QProcess") as process:
            for key in ("browser", "youtube", "audio", "network", "poweroff", "reboot", "suspend"):
                self.window.launch(key)
            process.assert_not_called()

    def test_power_dialog_starts_on_cancel(self):
        dialog = ChoiceDialog(self.window, "Napájení", "Test", [("Zpět", 0), ("Vypnout", 1)])
        dialog.show()
        self.app.processEvents()
        self.assertEqual(dialog.focusWidget().text(), "Zpět")
        QTest.keyClick(dialog.focusWidget(), Qt.Key.Key_Enter)
        self.assertEqual(dialog.result(), 0)
        self.assertFalse(dialog.isVisible())

    def test_remote_back_cancels_modal(self):
        dialog = ChoiceDialog(self.window, "Napájení", "Test", [("Zpět", 0), ("Vypnout", 1)])
        dialog.show()
        self.app.processEvents()
        QTest.keyClick(dialog.focusWidget(), Qt.Key.Key_Right)
        self.assertEqual(dialog.focusWidget().text(), "Vypnout")
        QTest.keyClick(dialog.focusWidget(), Qt.Key.Key_Back)
        self.assertEqual(dialog.result(), 0)
        self.assertFalse(dialog.isVisible())

    def test_cancel_power_menu_does_nothing(self):
        with patch("padtv.ui.ChoiceDialog.exec", return_value=0), patch.object(self.window, "launch") as launch:
            self.window.power_menu()
            launch.assert_not_called()

    def test_power_menu_dispatches_only_choice(self):
        for answer, command in [(1, "poweroff"), (2, "reboot"), (3, "suspend")]:
            with patch("padtv.ui.ChoiceDialog.exec", return_value=answer), patch.object(self.window, "launch") as launch:
                self.window.power_menu()
                launch.assert_called_once_with(command)

    def test_missing_application_is_reported(self):
        self.window.preview = False
        with patch("padtv.ui.executable_available", return_value=False), patch("padtv.ui.QProcess") as process:
            self.window.launch("browser")
            process.assert_not_called()
            self.assertIn("není nainstalovaná", self.window.notice)

    def test_all_screen_controls_fit_at_720p(self):
        self.window.resize(1280, 720)
        for page in ("home", "apps", "settings", "manage", "android", "store"):
            self.window.set_page(page)
            for button in self.window.buttons:
                self.assertTrue(self.window.rect().contains(button.geometry()))

    def test_navigation_tabs_activate_with_enter(self):
        next(button for button in self.window.buttons if button.text() == "Aplikace").setFocus()
        QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Return)
        self.assertEqual(self.window.page, "apps")
        next(button for button in self.window.buttons if button.text() == "Nastavení").setFocus()
        QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Return)
        self.assertEqual(self.window.page, "settings")

    def test_failed_child_is_reported_and_reaped(self):
        self.window.preview = False
        command = (sys.executable, "-c", "raise SystemExit(7)")
        with patch("padtv.ui.command_for", return_value=command), patch("padtv.ui.executable_available", return_value=True), patch.object(self.window, "activate_application"):
            self.window.spawn_application("browser", "Prohlížeč", command)
            child = self.window.processes["browser"]
            self.assertTrue(child.waitForFinished(5000))
        self.assertNotIn("browser", self.window.processes)
        self.assertIn("kód 7", self.window.notice)

    def test_running_application_activates_its_window(self):
        self.window.preview = False
        child = Mock()
        child.processId.return_value = 123
        self.window.processes["browser"] = child
        with patch.object(self.window, "activate_application") as activate, patch.object(self.window, "spawn_application") as spawn:
            self.window.launch("browser")
        self.assertEqual(activate.call_args.kwargs["pid"], 123)
        self.assertEqual(activate.call_args.kwargs["wait"], 12)
        spawn.assert_not_called()
        self.assertNotIn("už běží", self.window.notice)

    def test_repeated_click_during_activation_does_not_launch_duplicate(self):
        self.window.preview = False
        self.window.activations["browser"] = Mock()
        with patch.object(self.window, "activate_application") as activate, patch.object(self.window, "spawn_application") as spawn:
            self.window.launch("browser")
            self.window.launch("browser")
        activate.assert_not_called()
        spawn.assert_not_called()

    def test_first_launch_checks_for_existing_untracked_window(self):
        self.window.preview = False
        with patch("padtv.ui.executable_available", return_value=True), patch.object(self.window, "activate_application") as activate, \
             patch.object(self.window, "spawn_application") as spawn:
            self.window.launch("browser")
            spawn.assert_not_called()
            activate.call_args.kwargs["on_missing"]()
            spawn.assert_called_once()

    def test_youtube_uninstall_persists_after_restart(self):
        with patch("padtv.ui.ChoiceDialog.exec", return_value=2):
            self.window.app_details(YOUTUBE)
        self.assertFalse(any(app.id == "youtube" for app in self.window.library.list()))
        again = HomeWindow(preview=True, apps_dir=self.app_data.name)
        self.assertFalse(any(button.text() == "YouTube" for button in again.buttons))
        again.close()
        again.deleteLater()

    def test_cancel_uninstall_keeps_application(self):
        with patch("padtv.ui.ChoiceDialog.exec", return_value=0):
            self.window.app_details(YOUTUBE)
        self.assertEqual(self.window.library.list()[0], YOUTUBE)

    def test_store_web_install_uninstall_and_youtube_removal_survive_restart(self):
        product=next(p for p in self.window.products if p.id=='soundcloud')
        self.window.set_page('store')
        self.window.store_change(product,True)
        self.assertTrue(self.window.product_installed(product))
        self.window.store_change(product,False)
        self.window.store_change(next(p for p in self.window.products if p.id=='youtube'),False)
        self.assertFalse(self.window.product_installed(product))
        from padtv.apps import AppLibrary
        self.assertNotIn(YOUTUBE,AppLibrary(self.app_data.name).list())

    def test_store_preview_does_not_install_native_packages(self):
        product=next(p for p in self.window.products if p.id=='vlc')
        with patch('padtv.store_ui.QProcess') as process:
            self.window.store_change(product,True)
            process.assert_not_called()
        self.assertFalse(self.window.product_installed(product))

    def test_failed_native_install_does_not_add_launcher_icon(self):
        product=next(p for p in self.window.products if p.id=='vlc')
        self.window.preview=False
        with patch.object(self.window,'store_request') as request, patch.object(self.window,'refresh_store'):
            self.window.store_change(product,True)
            request.call_args.kwargs['callback']({'ok':False,'error':'Download failed'})
        self.assertFalse(any(a.id=='vlc' for a in self.window.library.list()))

    def test_android_preview_never_runs_system_commands(self):
        with patch("padtv.ui.QProcess") as process:
            for action in ("open", "prepare", "install", "remove", "launch"):
                self.window.android_task(action, "com.example.test")
            process.assert_not_called()

    def test_google_play_page_does_not_create_installed_app(self):
        product = next(p for p in self.window.products if p.id == 'youtube-tv')
        self.window.preview = False
        with patch.object(self.window, 'store_request') as request, patch.object(self.window, 'refresh_store'), patch.object(self.window, 'activate_application'):
            self.window.store_change(product, True)
            request.call_args.kwargs['callback']({'ok': True, 'opened': True, 'installed': False})
        self.assertFalse(any(a.id == product.id for a in self.window.library.list()))

    def test_android_unknown_inventory_preserves_app_and_known_inventory_reconciles(self):
        product = next(p for p in self.window.products if p.id == 'netflix-tv')
        saved = self.window.product_app(product)
        self.window.library.install(saved)
        self.window.preview = False
        with patch.object(self.window, 'store_request') as request:
            for known, packages, expected in ((False, [], True), (True, [], False), (True, [product.target], True)):
                self.window.refresh_store()
                request.call_args.kwargs['callback']({'ok': True, 'android_known': known, 'android': packages, 'error': 'Flatpak unavailable'})
                self.assertEqual(saved in self.window.library.list(), expected)

    def test_native_youtube_does_not_impersonate_web_app(self):
        product = next(p for p in self.window.products if p.id == 'youtube')
        self.window.library.install(UserApp('youtube', 'YouTube TV', 'android', 'com.google.android.youtube.tv'))
        self.assertFalse(self.window.product_installed(product))

    def test_android_inventory_migrates_legacy_apk_without_duplicate_icons(self):
        old = UserApp('youtube', 'YouTube', 'android', 'com.google.android.youtube.tv')
        self.window.library.install(old)
        self.window.preview = False
        with patch.object(self.window, 'store_request') as request:
            self.window.refresh_store()
            request.call_args.kwargs['callback']({'ok': True, 'android_known': True, 'android': [old.target]})
        native = [a for a in self.window.library.list() if a.target == old.target]
        self.assertEqual([a.id for a in native], ['youtube-tv'])

    def test_home_prioritizes_android_youtube_and_has_no_removed_defaults(self):
        product = next(p for p in self.window.products if p.id == 'youtube-tv')
        self.window.library.install(self.window.product_app(product))
        self.window.set_page('home')
        labels = [b.text() for b in self.window.buttons]
        self.assertIn(product.title, labels)
        self.assertNotIn('YouTube', labels)
        self.assertNotIn('Kodi', labels)
        self.assertNotIn('Jellyfin', labels)

    def test_android_record_kept_until_uninstall_success(self):
        app = UserApp("jellyfin", "Jellyfin", "android", "org.jellyfin.androidtv")
        self.window.library.install(app)
        with patch("padtv.ui.ChoiceDialog.exec", return_value=2), patch.object(self.window, "android_task") as task:
            self.window.app_details(app)
            self.assertEqual(task.call_args.args[:2], ("remove", "org.jellyfin.androidtv"))
        self.assertIn(app, self.window.library.list())


if __name__ == "__main__":
    unittest.main()
