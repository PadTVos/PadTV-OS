import json
from pathlib import Path
import tempfile
import unittest

from padtv.apps import AppLibrary, UserApp, YOUTUBE, validate_app


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.library = AppLibrary(self.root)

    def tearDown(self):
        self.directory.cleanup()

    def test_youtube_is_first_removable_default(self):
        self.library.install(UserApp("aaa", "AAA", "web", "https://example.com/"))
        self.assertEqual(self.library.list()[0], YOUTUBE)
        self.library.remove(YOUTUBE)
        reopened = AppLibrary(self.root)
        self.assertEqual([app.id for app in reopened.list()], ["aaa"])
        reopened.install(YOUTUBE)
        self.assertEqual(reopened.list()[0], YOUTUBE)

    def test_uninstall_removes_only_selected_profile(self):
        for app in ("youtube", "other"):
            path = self.root / "profiles" / app
            path.mkdir(parents=True)
            (path / "data").write_text("example")
        self.library.remove(YOUTUBE, remove_data=True)
        self.assertFalse((self.root / "profiles/youtube").exists())
        self.assertTrue((self.root / "profiles/other/data").exists())

    def test_invalid_manifest_cannot_inject_command_or_path(self):
        cases = [UserApp("../bad", "Bad", "web", "https://example.com"),
                 UserApp("bad", "Bad", "web", "file:///etc/passwd"),
                 UserApp("bad", "Bad", "android", "com.test;reboot"),
                 UserApp("bad", "Bad", "shell", "reboot")]
        for app in cases:
            with self.assertRaises(ValueError):
                self.library.install(app)

    def test_web_profile_is_per_application_and_no_shell(self):
        command = self.library.command(YOUTUBE)
        self.assertEqual(command[0], "chromium")
        self.assertIn("--app=https://www.youtube.com/", command)
        self.assertIn("--password-store=basic", command)
        self.assertTrue(any(arg.startswith("--user-data-dir=") for arg in command))
        self.assertNotIn("--no-sandbox", command)

    def test_corrupt_record_does_not_crash_library(self):
        (self.root / "apps/broken.json").write_text("{")
        self.assertEqual(self.library.list(), [YOUTUBE])


if __name__ == "__main__":
    unittest.main()
