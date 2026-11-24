import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import unittest
from unittest.mock import patch, Mock

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from padtv.ui import HomeWindow
from padtv.settings_ui import SettingsWindow, Prompt


class SettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = HomeWindow(preview=True, apps_dir=self.temp.name)
        self.home.resize(1280, 720)
        self.home.show()
        self.settings = SettingsWindow(self.home, preview=True)
        self.settings.show()
        self.app.processEvents()

    def tearDown(self):
        self.settings.close()
        self.home.close()
        self.settings.deleteLater()
        self.home.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def test_preview_cannot_change_system(self):
        with patch("padtv.settings_ui.QProcess") as process:
            for category in ("network", "bluetooth", "audio", "display", "system"):
                self.settings.load(category)
                self.settings.request(category + "-status")
            process.assert_not_called()

    def test_remote_navigation_and_back(self):
        self.settings.categories[0].setFocus()
        QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Down)
        self.assertEqual(self.app.focusWidget().text(), "Bluetooth")
        QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Return)
        self.assertEqual(self.settings.category, "bluetooth")
        QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Escape)
        self.assertFalse(self.settings.isVisible())

    def test_absent_wifi_has_no_fake_connect_button(self):
        self.settings.clear()
        self.settings.render({"devices": [], "aps": [], "wifi": False, "hardware": False, "vm": "kvm"})
        labels = [b.text() for b in self.settings.controls]
        self.assertNotIn("Zapnout Wi-Fi", labels)
        self.assertNotIn("Vyhledat sítě", labels)

    def test_remote_focus_returns_after_real_worker_finishes(self):
        self.settings.process = Mock()
        self.settings.process.canReadLine.return_value = False
        self.settings.focus_title = "Síť a Wi-Fi"
        for button in self.settings.controls:
            button.setEnabled(False)
        self.settings.result = {"ok": True, "data": {"devices": [], "aps": [], "wifi": False, "hardware": False, "vm": "kvm"}}
        self.settings.finished()
        self.app.processEvents()
        self.assertEqual(self.app.focusWidget().text(), "Síť a Wi-Fi")
        QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Down)
        self.assertEqual(self.app.focusWidget().text(), "Bluetooth")

    def test_onscreen_password_can_be_entered_and_canceled(self):
        prompt = Prompt(self.settings, "Wi-Fi", "Heslo", text=True, secret=True)
        prompt.show()
        self.app.processEvents()
        prompt.letters[10].click()
        prompt.shift()
        prompt.letters[10].click()
        self.assertEqual(prompt.input.text(), "qQ")
        QTest.keyClick(prompt.input, Qt.Key.Key_Escape)
        self.assertEqual(prompt.result(), 0)
        prompt.deleteLater()
