import os
from pathlib import Path
import shlex
import subprocess


def read_identity(path=Path('/etc/os-release')):
    result = {}
    for line in path.read_text().splitlines():
        if '=' not in line or line.lstrip().startswith('#'):
            continue
        key, value = line.split('=', 1)
        words = shlex.split(value)
        result[key] = words[0] if words else ''
    return result


def status():
    from . import API_VERSION
    identity = read_identity()
    vm = subprocess.run(['systemd-detect-virt', '--vm'], capture_output=True, text=True)
    return {'api_version': API_VERSION, 'identity': identity,
            'version': identity.get('BUILD_ID', identity.get('VERSION_ID', '')),
            'kernel': os.uname().release, 'hostname': os.uname().nodename,
            'vm': vm.stdout.strip() if vm.returncode == 0 else '',
            'live': Path('/run/live/medium/live/filesystem.squashfs').is_file(),
            'persistent': any(p.is_mount() for p in Path('/run/live/persistence').glob('*'))}

