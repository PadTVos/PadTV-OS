import unittest
from unittest.mock import patch

from padtv.actions import ACTIONS, command_for, executable_available
from padtv.navigation import next_in_direction


class ActionTests(unittest.TestCase):
    def test_unknown_command_is_rejected(self):
        for invalid in ("", "kodi; reboot", "https://example.com", "shutdown -h now"):
            with self.assertRaises(ValueError):
                command_for(invalid)

    def test_media_commands_are_unprivileged(self):
        for key in ACTIONS:
            command = command_for(key)
            self.assertIsInstance(command, tuple)
            self.assertNotIn(command[0], ("sh", "bash", "sudo", "pkexec"))
            self.assertNotIn("--no-sandbox", command)

    def test_missing_executable(self):
        with patch("padtv.actions.shutil.which", return_value=None):
            self.assertFalse(executable_available("browser"))

    def test_explicit_power_commands(self):
        for action in ('poweroff', 'reboot', 'suspend'):
            self.assertEqual(command_for(action), ('padtv-systemctl', 'power', action))


class NavigationTests(unittest.TestCase):
    def test_grid_and_boundaries(self):
        points = [(0, 0), (100, 0), (200, 0), (0, 100), (100, 100)]
        self.assertEqual(next_in_direction(0, points, "right"), 1)
        self.assertEqual(next_in_direction(1, points, "down"), 4)
        self.assertEqual(next_in_direction(4, points, "up"), 1)
        self.assertEqual(next_in_direction(0, points, "left"), 0)
        self.assertEqual(next_in_direction(4, points, "down"), 4)

    def test_prefers_same_column(self):
        points = [(100, 0), (100, 200), (280, 180)]
        self.assertEqual(next_in_direction(0, points, "down"), 1)


if __name__ == "__main__":
    unittest.main()
