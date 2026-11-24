"""Explicit integration checks in a disposable Live VM; never run on a real PC.

Run as the TV user with sudo available. Restarts the UI and Core daemon and
changes display mode with rollback. Does not install to disk or power off.
"""
import json
import os
import subprocess
import time
import uuid

assert subprocess.run(['systemd-detect-virt','--vm','--quiet']).returncode == 0, 'Disposable VM required'
assert os.environ.get('XDG_SESSION_TYPE') == 'wayland', 'Wayland session required'

def run(*argv):
    return subprocess.check_output(argv,text=True).strip()

def wait(predicate, seconds=15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if predicate(): return
        time.sleep(.3)
    raise AssertionError('Timed out')

info=json.loads(run('padtv-systemctl','info'))
assert info['ok'] and info['data']['identity']['ID']=='padtv'
assert json.loads(run('padtv-systemctl','devices'))['ok']
assert json.loads(run('padtv-systemctl','services'))['ok']
assert json.loads(run('padtv-systemctl','service','network','restart'))['ok']
denied=subprocess.run(['sudo','-n','runuser','-u','nobody','--','padtv-systemctl','service','network','restart'],capture_output=True,text=True)
assert denied.returncode and 'AccessDenied' in denied.stdout
print('API_IDENTITY_DEVICES_SERVICES_AUTH_PASS',flush=True)

old=run('systemctl','show','padtv-system.service','--value','-p','MainPID')
subprocess.run(['sudo','-n','systemctl','kill','--signal=SIGKILL','padtv-system.service'],check=True)
wait(lambda: run('systemctl','show','padtv-system.service','--value','-p','MainPID') not in ('0',old))
wait(lambda: subprocess.run(['padtv-systemctl','info'],capture_output=True).returncode==0)
assert json.loads(run('padtv-systemctl','info'))['ok']
print('API_CRASH_RECOVERY_PASS',flush=True)

app=subprocess.Popen(['systemd-run','--user','--scope','--collect','--unit=padtv-app-core-qa-'+uuid.uuid4().hex,'thunar'])
wait(lambda: subprocess.run(['wlrctl','toplevel','find','app_id:thunar']).returncode==0)
old=run('systemctl','--user','show','padtv-shell.service','--value','-p','MainPID')
subprocess.run(['systemctl','--user','kill','--signal=SIGKILL','padtv-shell.service'],check=True)
wait(lambda: run('systemctl','--user','show','padtv-shell.service','--value','-p','MainPID') not in ('0',old))
assert subprocess.run(['wlrctl','toplevel','find','app_id:thunar']).returncode==0
run('wlrctl','toplevel','focus','app_id:thunar')
print('SHELL_CRASH_RECOVERY_APP_SURVIVES_PASS',flush=True)

outputs=json.loads(run('wlr-randr','--json'))
output=next(o for o in outputs if o['enabled'] and sum(bool(m.get('current')) for m in o['modes']))
current=next(m for m in output['modes'] if m.get('current'))
other=next(m for m in output['modes'] if not m.get('current') and 1024<=m['width']<=1920)
def label(mode): return f"{mode['width']}x{mode['height']}@{mode['refresh']:.3f}Hz"
process=subprocess.Popen(['padtv-system-settings'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
process.stdin.write(json.dumps(dict(action='display-set',output=output['name'],mode=label(other)))+'\n'); process.stdin.flush()
reply=json.loads(process.stdout.readline())
assert reply.get('event')=='display-confirm', reply
changed=json.loads(run('wlr-randr','--json'))
assert any(m.get('current') and m['width']==other['width'] and m['height']==other['height'] for o in changed if o['name']==output['name'] for m in o['modes'])
process.wait(timeout=20)
assert process.returncode==0, process.stderr.read()
restored=json.loads(run('wlr-randr','--json'))
assert any(m.get('current') and m['width']==current['width'] and m['height']==current['height'] and m['refresh']==current['refresh'] for o in restored if o['name']==output['name'] for m in o['modes'])
print('WAYLAND_DISPLAY_TIMED_ROLLBACK_PASS',flush=True)
# Cleanup is idempotent: the file manager can already have closed its window.
subprocess.run(['wlrctl','toplevel','close','app_id:thunar'], check=False)
print('CORE_INTEGRATION_PASS',flush=True)
