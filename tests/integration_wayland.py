import http.server
import os
import re
import socketserver
import sys
import tempfile
import threading
import time
import subprocess
from pathlib import Path
assert subprocess.run(['systemd-detect-virt', '--vm', '--quiet']).returncode == 0, 'Disposable VM required'
sys.path.insert(0,'/usr/share/padtv')
os.environ.update(DISPLAY=':0',WAYLAND_DISPLAY='wayland-0',XDG_SESSION_TYPE='wayland',PADTV_MANAGED_SESSION='1',PYTHONPATH='/usr/share/padtv',XDG_RUNTIME_DIR=f'/run/user/{os.getuid()}')
from PyQt6.QtWidgets import QApplication
from padtv.ui import HomeWindow
from padtv.apps import UserApp
from padtv import windows

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        data=b'<html><head><title>Same test title</title></head><body style="background:#123;color:white"><h1>PadTV focus test</h1></body></html>'
        self.send_response(200); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self,*args): pass
server=socketserver.TCPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
app=QApplication([])
app.setDesktopFileName('padtv-focus-test')
folder=tempfile.TemporaryDirectory(prefix='padtv-focus-test-')
home=HomeWindow(preview=False,apps_dir=folder.name)
home.showFullScreen()
app.processEvents()
apps=[UserApp('focus-a','A','web',f'http://127.0.0.1:{server.server_address[1]}/a'),UserApp('focus-b','B','web',f'http://127.0.0.1:{server.server_address[1]}/b')]
for item in apps: home.library.install(item)
def wait(predicate,timeout=30):
    deadline=time.monotonic()+timeout
    last=0
    while time.monotonic()<deadline:
        app.processEvents()
        if predicate(): return
        if time.monotonic()-last>5:
            last=time.monotonic()
            rows=windows.parse_windows(windows.run('wmctrl','-lpxS'))
            print('WAIT',home.activations.keys(),[(r,windows.process_args(r['pid'])) for r in rows if 'chromium' in r['class']], 'expected',home.library.command(apps[0]),flush=True)
        time.sleep(.05)
    raise AssertionError('Timed out waiting for GUI state')
def entries(item):
    request={'key':'user:'+item.id,'command':home.library.command(item)}
    return [w for w in windows.parse_windows(windows.run('wmctrl','-lpxS')) if windows.matches(w,request)]
def active():
    return int(re.search(r'0x[0-9a-fA-F]+',windows.run('xprop','-root','_NET_ACTIVE_WINDOW'))[0],16)
def front(window):
    windows.run('wlrctl','toplevel','focus','app_id:padtv-focus-test')
    app.processEvents()
other=None
try:
    home.launch_user(apps[0])
    wait(lambda:len(entries(apps[0]))==1 and not home.activations)
    first=entries(apps[0])[0]
    front(home)
    for _ in range(3): home.launch_user(apps[0])
    wait(lambda:active()==int(first['id'],16) and not home.activations)
    assert len(entries(apps[0]))==1
    print('REPEATED_CLICK_SAME_WINDOW',first,flush=True)
    front(home); home.launch_user(apps[1])
    wait(lambda:len(entries(apps[1]))==1 and not home.activations)
    second=entries(apps[1])[0]
    front(home); home.launch_user(apps[0])
    wait(lambda:active()==int(first['id'],16) and not home.activations)
    assert first['id']!=second['id']
    print('SAME_TITLE_DIFFERENT_PROFILES_PASS',flush=True)
    windows.run('wmctrl','-i','-Y',first['id'])
    front(home); home.launch_user(apps[0])
    wait(lambda:active()==int(first['id'],16) and not home.activations)
    print('MINIMIZED_WINDOW_RESTORED',flush=True)
    other=HomeWindow(preview=False,apps_dir=folder.name)
    other.showFullScreen(); app.processEvents(); front(other)
    other.launch_user(apps[0])
    wait(lambda:active()==int(first['id'],16) and not other.activations)
    assert 'user:focus-a' not in other.processes
    assert len(entries(apps[0]))==1
    print('UNTRACKED_INSTANCE_REUSED',flush=True)
    # Close the active application with the same compositor shortcut as users.
    windows.run('wmctrl','-ia',second['id'])
    windows.run('wlrctl','keyboard','type','w','modifiers','CTRL,SHIFT')
    wait(lambda:not entries(apps[1]))
    app.processEvents(); front(home); home.launch_user(apps[1])
    wait(lambda:len(entries(apps[1]))==1 and not home.activations)
    print('CLOSED_WINDOW_REOPENED',entries(apps[1])[0],flush=True)
    assert not home.clock.isActive(), 'Home clock should sleep behind another app'
    print('BACKGROUND_CLOCK_STOPPED',flush=True)
    print('FOCUS_INTEGRATION_PASS',flush=True)
finally:
    for item in apps:
        for window in entries(item):
            windows.run('wmctrl','-ic',window['id'])
    for _ in range(30): app.processEvents(); time.sleep(.1)
    home.close()
    if other: other.close()
    server.shutdown()
    folder.cleanup()

