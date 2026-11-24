import importlib.util
import tempfile
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch
from padtv_core import identity, power, services, client
from padtv_core.session import eligible
from padtv import session, windows


class CoreTests(unittest.TestCase):
    def test_privileges_require_an_active_local_tv_login(self):
        props = dict(Active=True, Remote=False, Type='wayland', Class='user', Service='greetd', TTY='tty7')
        self.assertTrue(eligible(props))
        for field, value in [('Active',False),('Remote',True),('Type','tty'),('Class','greeter'),('Service','sshd'),('TTY','tty1')]:
            with self.subTest(field=field):
                self.assertFalse(eligible({**props, field:value}))
        self.assertFalse(eligible({}))

    def test_absolute_chromium_executable_keeps_profile_identity(self):
        command = ['chromium', '--user-data-dir=/profile/a']
        self.assertEqual(session.app_id('user:a', command), session.app_id('user:a', ['/usr/bin/chromium', *command[1:]]))

    def test_lazy_xwayland_empty_list_is_not_an_error(self):
        result = Mock(returncode=1, stderr='Cannot get client list properties.\n(_NET_CLIENT_LIST_STACKING)')
        with patch('padtv.session.wayland', return_value=True), patch.object(windows.subprocess, 'run', return_value=result):
            self.assertEqual(windows.run('wmctrl', '-lpxS'), '')

    def test_unavailable_xwayland_display_is_still_an_error(self):
        result = Mock(returncode=1, stderr='Cannot open display.')
        with patch('padtv.session.wayland', return_value=True), patch.object(windows.subprocess, 'run', return_value=result):
            with self.assertRaises(RuntimeError): windows.run('wmctrl', '-lpxS')

    def test_os_release_is_data_not_executable(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'os-release'
            path.write_text('ID=padtv\nID_LIKE=debian\nPRETTY_NAME="PadTV System Core"\nEVIL="$(touch /tmp/wrong)"\n')
            result = identity.read_identity(path)
            self.assertEqual(result['ID'], 'padtv')
            self.assertEqual(result['EVIL'], '$(touch /tmp/wrong)')

    def test_service_control_rejects_arbitrary_units_and_operations(self):
        for name, operation in [('sshd.service','restart'),('network','exec'),('../network','stop'),('network;reboot','start')]:
            with self.assertRaises(ValueError): services.validate(name, operation)
        self.assertEqual(services.validate('bluetooth','restart'), ('bluetooth.service','RestartUnit'))

    def test_unsupported_suspend_never_attempts_sleep(self):
        manager = Mock()
        manager.CanSuspend.return_value = 'na'
        with patch.object(power, 'manager', return_value=manager):
            with self.assertRaises(RuntimeError): power.perform(None, 'suspend')
        manager.Suspend.assert_not_called()

    def test_supported_suspend_uses_logind_without_password_dialog(self):
        manager = Mock()
        manager.CanSuspend.return_value = 'yes'
        with patch.object(power, 'manager', return_value=manager):
            self.assertTrue(power.perform(None, 'suspend')['accepted'])
        manager.Suspend.assert_called_once_with(False)

    def test_unknown_power_action_is_rejected(self):
        with patch.object(power, 'manager') as manager:
            with self.assertRaises(ValueError): power.perform(None, 'hibernate; reboot')
            manager.assert_not_called()

    def test_windows_api_refuses_system_actions(self):
        with patch.object(client.sys, 'platform', 'win32'):
            with self.assertRaises(RuntimeError): client.call('Power', 'poweroff')

    def test_wayland_web_identity_tracks_profile_not_title(self):
        a = session.app_id('user:a', ['chromium','--user-data-dir=/profile/a','--app=https://a.test'])
        self.assertEqual(a, session.app_id('user:a', ['chromium','--user-data-dir=/profile/a','--app=https://b.test']))
        self.assertNotEqual(a, session.app_id('user:b', ['chromium','--user-data-dir=/profile/b']))

    def test_managed_apps_have_independent_scopes_and_safe_argv(self):
        with patch.dict('os.environ', {'PADTV_MANAGED_SESSION':'1','WAYLAND_DISPLAY':'wayland-0','XDG_SESSION_TYPE':'wayland'}):
            command = session.application_command('user:a', ['chromium','--user-data-dir=/with spaces','--app=https://a.test'])
        self.assertEqual(command[:3], ['systemd-run','--user','--scope'])
        self.assertIn('--user-data-dir=/with spaces', command)
        self.assertIn('--ozone-platform=x11', command)
        self.assertIn('--', command)

    def test_wayland_focus_uses_exact_app_id(self):
        with patch('padtv.session.wayland', return_value=True), patch.object(windows.subprocess, 'run', return_value=Mock(returncode=0)) as find, patch.object(windows,'run') as activate:
            self.assertTrue(windows.activate({'key':'files','command':['thunar']})['found'])
        self.assertEqual(find.call_args.args[0], ['wlrctl','toplevel','find','app_id:thunar'])
        activate.assert_called_once_with('wlrctl','toplevel','focus','app_id:thunar')

    def test_installer_rejects_host_root_before_changing_files(self):
        fake = Mock()
        fake.globalstorage.value.return_value = '/'
        path = Path(__file__).resolve().parents[1]/'packaging/installer/padtv-finalize/main.py'
        spec = importlib.util.spec_from_file_location('padtv_finalize_test', path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'libcalamares':fake}):
            spec.loader.exec_module(module)
            self.assertIsNotNone(module.run())
        fake.utils.target_env_call.assert_not_called()
