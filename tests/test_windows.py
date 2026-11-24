import unittest
import os
from unittest.mock import patch
from padtv import windows


class WindowTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'WAYLAND_DISPLAY':'', 'XDG_SESSION_TYPE':'x11'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_chromium_rewritten_process_title_retains_profile_identity(self):
        args=windows.parse_process_args(b'/usr/lib/chromium/chromium --user-data-dir=/tmp/with spaces/profile --app=http://localhost/\0')
        self.assertEqual(windows.option(args,'--user-data-dir'),'/tmp/with spaces/profile')

    def test_normal_argv_and_quoted_title_preserve_profile_spaces(self):
        normal=windows.parse_process_args(b'chromium\0--user-data-dir=/tmp/with spaces\0--app=http://localhost\0')
        quoted=windows.parse_process_args(b'chromium --user-data-dir="/tmp/with spaces" --app=http://localhost\0')
        self.assertEqual(windows.option(normal,'--user-data-dir'),'/tmp/with spaces')
        self.assertEqual(windows.option(quoted,'--user-data-dir'),'/tmp/with spaces')

    def test_parser_ignores_title_spacing_and_invalid_ids(self):
        entries = windows.parse_windows('0x00a00123 0 123 youtube.Chromium padtv A long title with spaces\ninvalid 0 44 kodi.kodi host title')
        self.assertEqual(entries, [{"id":"0x00a00123", "pid":123, "class":"youtube.chromium"}])

    def test_web_profiles_with_same_title_are_not_confused(self):
        rows = windows.parse_windows('0x00000001 0 10 chromium.Chromium host YouTube\n0x00000002 0 20 chromium.Chromium host YouTube')
        request={"key":"user:youtube", "command":["chromium", "--user-data-dir=/profiles/youtube"]}
        with patch.object(windows, "process_args", side_effect=lambda pid:["chromium", "--user-data-dir=/profiles/" + ("youtube" if pid==10 else "other")]):
            self.assertEqual(windows.find_window(rows, request)["id"], "0x00000001")

    def test_most_recent_matching_window_is_selected(self):
        rows = windows.parse_windows('0x00000001 0 10 thunar.Thunar host Folder 1\n0x00000002 0 10 thunar.Thunar host Folder 2')
        with patch.object(windows, "process_args", return_value=["thunar"]):
            self.assertEqual(windows.find_window(rows, {"key":"files"})["id"], "0x00000002")

    def test_browser_does_not_activate_a_separate_web_app(self):
        window={"pid":10, "class":"chromium.chromium"}
        with patch.object(windows, "process_args", return_value=["chromium", "--user-data-dir=/youtube", "--app=https://youtube.com"]):
            self.assertFalse(windows.matches(window, {"key":"browser"}))

    def test_child_process_window_matches_launcher(self):
        with patch.object(windows, "parent_pid", side_effect=lambda pid: {22:11, 11:1}.get(pid,0)):
            self.assertTrue(windows.descends_from(22,11))
            self.assertFalse(windows.descends_from(22,33))

    def test_parent_cycle_does_not_hang(self):
        with patch.object(windows, "parent_pid", return_value=22):
            self.assertFalse(windows.descends_from(22,33))

    def test_existing_window_uses_numeric_activation_without_shell(self):
        with patch.object(windows, "run", side_effect=['0x00000001 0 10 kodi.kodi host Kodi', '']) as run, \
             patch.object(windows, "process_args", return_value=["kodi"]):
            self.assertTrue(windows.activate({"key":"kodi"})["found"])
            run.assert_any_call("wmctrl", "-ia", "0x00000001")

    def test_android_only_matches_padtv_compositor(self):
        with patch.object(windows, "process_args", return_value=["weston", "--socket=another-desktop"]):
            self.assertFalse(windows.matches({"pid":10, "class":"weston.weston"}, {"key":"android-shell"}))
