"""Finalize ONLY Calamares' mounted target after its destructive confirmation."""
from pathlib import Path
import libcalamares


def run():
    root = Path(libcalamares.globalstorage.value('rootMountPoint') or '/')
    if not root.is_absolute() or root == Path('/') or not root.is_mount() or not (root/'etc/debian_version').is_file():
        return ('Neplatný cíl instalace', 'PadTV odmítl upravit soubory mimo připojený cílový systém.')
    # Live media grants its temporary TV account sudo; installed TV sessions do not.
    for name in ('live', 'live-config'):
        (root/'etc/sudoers.d'/name).unlink(missing_ok=True)
    for name in ('policy-rc.d',):
        (root/'usr/sbin'/name).unlink(missing_ok=True)
    for command in (['/usr/lib/padtv/padtv-account'], ['usermod', '-L', 'padtv'],
                    ['systemctl', 'enable', 'padtv.service', 'padtv-system.service', 'NetworkManager.service', 'bluetooth.service'],
                    ['systemctl', 'set-default', 'graphical.target'],
                    ['plymouth-set-default-theme', 'padtv']):
        result = libcalamares.utils.target_env_call(command)
        if result != 0:
            return ('Dokončení PadTV selhalo', 'Systémovou konfiguraci se nepodařilo dokončit: '+command[0])
    return None
