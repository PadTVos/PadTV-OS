from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from padtv import android


class AndroidTests(unittest.TestCase):
    def test_list_parser_accepts_tv_package(self):
        apps = android.parse_apps("Name: Jellyfin\npackageName: org.jellyfin.androidtv\ncategories:\n\tandroid.intent.category.LEANBACK_LAUNCHER\nName: Fake\npackageName: bad;reboot\n")
        self.assertEqual(apps, [{"name": "Jellyfin", "package": "org.jellyfin.androidtv"}])

    def test_bad_package_rejected_before_system_actions(self):
        with patch.object(android, "ensure_session") as session:
            with self.assertRaises(android.AndroidError):
                android.execute("remove", "com.foo; reboot")
            session.assert_not_called()

    def test_reported_waydroid_failure_is_not_silently_successful(self):
        result = subprocess.CompletedProcess([], 0, "", "ERROR: WayDroid session is stopped")
        with patch("subprocess.run", return_value=result):
            with self.assertRaises(android.AndroidError):
                android.run(["waydroid", "app", "list"])

    def test_apk_arm_only_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "app.apk"
            apk.touch()
            result = subprocess.CompletedProcess([], 0, "package: name='org.example.app'\napplication-label:'Test'\nnative-code: 'arm64-v8a'\n", "")
            with patch.object(android, "run", return_value=result):
                with self.assertRaises(android.AndroidError):
                    android.apk_info(apk)

    def test_waydroid_startup_retry_is_not_a_final_failure(self):
        result = subprocess.CompletedProcess([], 0, "", "Failed to get service waydroidplatform, trying again...")
        with patch("subprocess.run", return_value=result):
            self.assertEqual(android.run(["waydroid", "show-full-ui"]), result)

    def test_apk_install_is_user_install_and_verified(self):
        info = {"name": "Jellyfin", "package": "org.jellyfin.androidtv", "path": "/tmp/with spaces.apk"}
        with patch.object(android, "apk_info", return_value=info), patch.object(android, "ensure_session"), patch.object(android, "run") as command, patch.object(android, "app_list", return_value=[info]):
            self.assertEqual(android.execute("install", info["path"]), info)
            command.assert_called_once_with(["waydroid", "app", "install", info["path"]], timeout=180)

    def test_failed_uninstall_is_not_acknowledged(self):
        with patch.object(android, "ensure_session"), patch.object(android, "run"), patch.object(android, "app_list", return_value=[{"package": "org.example.app"}]), patch("padtv.android.time.monotonic", side_effect=[0, 31]):
            with self.assertRaises(android.AndroidError):
                android.execute("remove", "org.example.app")

    def test_waits_for_asynchronous_install(self):
        with patch.object(android, "app_list", side_effect=[[], [], [{"package": "org.example.app"}]]), patch("padtv.android.time.sleep") as sleep:
            android.wait_package("org.example.app", True)
            self.assertEqual(sleep.call_count, 2)

    def test_uninstall_falls_back_to_android_confirmation_without_root(self):
        with patch.object(android, "ensure_session"), patch.object(android, "run", side_effect=[android.AndroidError("Failed to uninstall package"), None, None]) as command, patch.object(android, "wait_package") as verified:
            self.assertEqual(android.execute("remove", "org.example.app"), {"removed": "org.example.app"})
            self.assertEqual(command.call_args_list[1].args[0], ["waydroid", "app", "intent", "android.intent.action.DELETE", "package:org.example.app"])
            self.assertEqual(command.call_args.args[0], ["waydroid", "show-full-ui"])
            verified.assert_called_once_with("org.example.app", present=False, timeout=180)

    def test_running_container_is_not_ready_until_android_boots(self):
        runtime = MagicMock()
        runtime.stat.return_value.st_uid = 1000
        boot_states = iter(["0", "1"])
        def command(argv, **kwargs):
            return subprocess.CompletedProcess(argv, 0, next(boot_states) if argv[:3] == ["waydroid", "prop", "get"] else "", "")
        with patch.object(android, "require_initialized"), patch.object(android, "Path", return_value=runtime), patch("padtv.android.os.getuid", return_value=1000, create=True), patch.dict("os.environ", {"DISPLAY": ":0"}), patch.object(android, "status", return_value={"running": True}), patch.object(android, "run", side_effect=command) as run, patch("padtv.android.time.sleep") as sleep:
            android.ensure_session()
            self.assertEqual(sum(call.args[0][:3] == ["waydroid", "prop", "get"] for call in run.call_args_list), 2)
            sleep.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
