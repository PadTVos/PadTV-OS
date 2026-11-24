"""Run explicitly in a disposable VM with GAPPS ready, without a Google account.

Requires Google Play installed and YouTube/Netflix TV absent. Opens real Play
pages and verifies that merely opening them never adds installed app records.
"""
import subprocess
import tempfile
import time
from PyQt6.QtWidgets import QApplication
from padtv.ui import HomeWindow

assert subprocess.run(['systemd-detect-virt', '--vm', '--quiet']).returncode == 0
app = QApplication([])
app.setDesktopFileName('padtv-play-qa')

def wait(predicate, seconds=120):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        if predicate(): return
        time.sleep(.05)
    raise AssertionError('Google Play integration timed out')

with tempfile.TemporaryDirectory(prefix='padtv-play-qa-') as folder:
    window = HomeWindow(preview=False, apps_dir=folder)
    messages = []
    original_toast = window.toast
    def record_toast(message):
        messages.append(message)
        original_toast(message)
    window.toast = record_toast
    window.showFullScreen()
    window.set_page('store')
    wait(lambda: window.store_native is not None and not window.store_process)
    assert window.store_native.get('google_play')
    assert window.store_native.get('android_known')
    assert not window.store_native.get('android_error')
    print('GOOGLE_PLAY_REAL_INVENTORY_PASS', flush=True)
    for name in ('youtube-tv', 'netflix-tv'):
        product = next(p for p in window.products if p.id == name)
        assert not window.product_installed(product), 'Use a VM without these apps installed'
        messages.clear()
        window.store_change(product, True)
        wait(lambda: not window.store_busy and not window.store_process and not window.activations)
        assert not window.product_installed(product)
        assert not any(a.id == name for a in window.library.list())
        assert any('Otevřeno Google Play' in message for message in messages), messages
        print(name.upper() + '_PLAY_OPEN_WITHOUT_FAKE_INSTALL_PASS', flush=True)
    assert any(a.id == 'youtube' and a.kind == 'web' for a in window.library.list())
    window.close()
print('GOOGLE_PLAY_INTEGRATION_PASS', flush=True)
