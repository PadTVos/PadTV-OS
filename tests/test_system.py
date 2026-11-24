import io
import os
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from padtv import system


XRANDR = """Screen 0: minimum 320 x 200, current 1600 x 900, maximum 16384 x 16384
Virtual-1 connected primary 1600x900+0+0 (normal left inverted right x axis y axis)
   1600x900     60.00*+
   1280x720     60.00
HDMI-1 disconnected (normal left inverted right x axis y axis)
"""


class SystemTests(unittest.TestCase):
    def setUp(self):
        # These fixtures exercise the retained X11 fallback, irrespective of host.
        self.env = patch.dict(os.environ, {'WAYLAND_DISPLAY':'', 'XDG_SESSION_TYPE':'x11'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_display_timeout_restores_original_mode(self):
        with patch.object(system, "run", return_value=XRANDR) as run, patch.object(system, "emit"), \
             patch.object(system.select, "select", return_value=([], [], [])):
            system.display({"action": "display-set", "output": "Virtual-1", "mode": "1280x720"})
        calls = [call.args for call in run.call_args_list]
        self.assertIn(("xrandr", "--output", "Virtual-1", "--mode", "1280x720"), calls)
        self.assertIn(("xrandr", "--output", "Virtual-1", "--mode", "1600x900"), calls)

    def test_confirmed_display_change_is_kept(self):
        with patch.object(system, "run", return_value=XRANDR) as run, patch.object(system, "emit"), \
             patch.object(system.select, "select", return_value=([1], [], [])), \
             patch.object(system.sys, "stdin", io.StringIO('{"confirm":true}\n')):
            system.display({"action": "display-set", "output": "Virtual-1", "mode": "1280x720"})
        self.assertNotIn(("xrandr", "--output", "Virtual-1", "--mode", "1600x900"), [c.args for c in run.call_args_list])

    def test_invalid_display_does_not_execute_change(self):
        with patch.object(system, "run", return_value=XRANDR) as run:
            with self.assertRaises(ValueError):
                system.display({"action": "display-set", "output": "Virtual-1", "mode": "$(evil)"})
            self.assertEqual(run.call_count, 1)

    def test_closed_input_restores_display(self):
        with patch.object(system, "run", return_value=XRANDR) as run, patch.object(system, "emit"), \
             patch.object(system.select, "select", return_value=([1], [], [])), \
             patch.object(system.sys, "stdin", io.StringIO('')):
            with self.assertRaises(ValueError):
                system.display({"action": "display-set", "output": "Virtual-1", "mode": "1280x720"})
        self.assertIn(("xrandr", "--output", "Virtual-1", "--mode", "1600x900"), [c.args for c in run.call_args_list])

    def test_wifi_security_distinguishes_password_and_enterprise(self):
        for flags, expected in [(0x100, "wpa-psk"), (0x400, "sae"), (0x500, "wpa-psk"), (0x200, "enterprise"), (0x800, "owe")]:
            self.assertEqual(system.wifi_security({"RsnFlags": flags}), expected)
        self.assertEqual(system.wifi_security({"Flags": 1}), "wep")
        self.assertEqual(system.wifi_security({}), "open")

    def test_activation_failure_is_not_success(self):
        with patch.object(system, "props", return_value={"State": 4}):
            with self.assertRaises(RuntimeError):
                system.wait_network(None, "/active")

    def test_volume_is_bounded(self):
        with patch.object(system, "run", return_value="[]") as run:
            with self.assertRaises(ValueError):
                system.audio({"action": "audio-volume", "volume": 999})
            self.assertEqual(run.call_count, 1)

    def test_no_audio_output_returns_empty_state(self):
        with patch.object(system, "run", return_value="[]"):
            self.assertEqual(system.audio({"action": "audio-status"})["sinks"], [])

    def test_audio_preferences_survive_new_worker(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"audio.json"
            with patch.object(system, "audio_settings_path", return_value=path):
                system.save_audio({"default": "hdmi", "volume": 37, "mute": True})
                with patch.object(system, "run", return_value='[{"name":"hdmi"}]') as run:
                    system.restore_audio()
                self.assertIn(("wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SINK@", "37%"), [c.args for c in run.call_args_list])
                self.assertIn(("wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1"), [c.args for c in run.call_args_list])

    def test_invalid_saved_volume_does_not_change_audio(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"audio.json"
            path.write_text(json.dumps({"volume": 300, "sink": "hdmi", "mute": False}))
            with patch.object(system, "audio_settings_path", return_value=path), patch.object(system, "run") as run:
                with self.assertRaises(ValueError):
                    system.restore_audio()
                run.assert_not_called()
