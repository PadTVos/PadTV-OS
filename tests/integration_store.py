"""Run explicitly in a disposable VM with VLC installed and its window open."""
import os,subprocess,tempfile,time
assert subprocess.run(['systemd-detect-virt','--vm','--quiet']).returncode==0
from PyQt6.QtWidgets import QApplication
from padtv.ui import HomeWindow

app=QApplication([])
app.setDesktopFileName('padtv-store-qa')
def wait(predicate,seconds=45):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        app.processEvents()
        if predicate(): return
        time.sleep(.05)
    raise AssertionError('Store integration timed out')

with tempfile.TemporaryDirectory(prefix='padtv-store-qa-') as folder:
    window=HomeWindow(preview=False,apps_dir=folder)
    window.showFullScreen()
    window.set_page('store')
    wait(lambda:window.store_native is not None and not window.store_process)
    vlc=next(p for p in window.products if p.id=='vlc')
    assert window.product_installed(vlc)
    assert any(a.id=='vlc' for a in window.library.list())
    print('STORE_NATIVE_INVENTORY_RECONCILIATION_PASS',flush=True)
    window.launch_user(window.product_app(vlc))
    wait(lambda:not window.activations)
    assert 'user:vlc' not in window.processes, 'Existing VLC window must be reused'
    for _ in range(3): window.launch_user(window.product_app(vlc))
    wait(lambda:not window.activations)
    assert 'user:vlc' not in window.processes
    print('STORE_EXISTING_FLATPAK_WINDOW_REUSED_PASS',flush=True)
    web=next(p for p in window.products if p.id=='soundcloud')
    window.store_change(web,True)
    assert window.product_installed(web)
    window.store_change(web,False)
    assert not window.product_installed(web)
    print('STORE_WEB_INSTALL_REMOVE_PASS',flush=True)
    # This VM owns its test app; the real provider refuses uninstall while running.
    subprocess.run(['flatpak','kill','org.videolan.VLC'],capture_output=True)
    wait(lambda: 'org.videolan.VLC' not in subprocess.check_output(['flatpak','ps','--columns=application'],text=True))
    window.store_change(vlc,False)
    wait(lambda:not window.store_busy and not window.store_process)
    assert not window.product_installed(vlc)
    assert not any(a.id=='vlc' for a in window.library.list())
    print('STORE_FLATPAK_UNINSTALL_VERIFIED_PASS',flush=True)
    window.close()
print('STORE_INTEGRATION_PASS',flush=True)
