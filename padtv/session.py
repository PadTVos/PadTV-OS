"""Compositor-specific launch and window identity, separate from the TV UI."""
import hashlib
import os
from pathlib import Path
import uuid


def wayland():
    return bool(os.environ.get('WAYLAND_DISPLAY')) and os.environ.get('XDG_SESSION_TYPE') == 'wayland'


def app_id(key, command):
    if len(command) == 3 and command[:2] in (['flatpak', 'run'], ('flatpak', 'run')):
        # Some upstream clients publish a legacy Wayland app_id inside Flatpak.
        return {'org.videolan.VLC': 'vlc'}.get(command[2], command[2])
    if command and Path(command[0]).name == 'chromium':
        profile = next((arg.partition('=')[2] for arg in command if arg.startswith('--user-data-dir=')), '')
        return 'padtv-web-' + hashlib.sha256(profile.encode()).hexdigest()[:20] if profile else 'padtv-browser'
    return {'files': 'thunar', 'android-shell': 'weston', 'home': 'padtv'}.get(key)


def application_command(key, command):
    command = list(command)
    if wayland() and Path(command[0]).name == 'chromium':
        # Chromium's native web-app IDs omit the user-data directory. Keep web
        # apps on Xwayland so exact process/profile matching remains reliable.
        command[1:1] = ['--ozone-platform=x11', '--class=' + app_id(key, command)]
    if os.environ.get('PADTV_MANAGED_SESSION') == '1':
        # Separate cgroups: restarting the shell leaves user apps alive.
        command = ['systemd-run', '--user', '--scope', '--collect', '--quiet',
                   '--unit=padtv-app-' + uuid.uuid4().hex, '--', *command]
    return command
