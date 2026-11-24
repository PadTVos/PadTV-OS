"""Find and activate an application's X11 window without blocking the Qt thread.

Match process ancestry, exact Chromium profile or a known native window class.
Window titles are deliberately not identities: two web apps can have the same title.
"""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


def run(*args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=3,
                            env={**os.environ, "LC_ALL": "C.UTF-8"})
    if result.returncode:
        # Labwc starts Xwayland lazily. Before its first client, EWMH has no
        # window-list property yet; this is an empty list, not a launch failure.
        from .session import wayland
        if (args == ('wmctrl', '-lpxS') and wayland()
                and 'Cannot get client list properties.' in result.stderr
                and '_NET_CLIENT_LIST' in result.stderr):
            return ''
        raise RuntimeError(result.stderr.strip() or "Správce oken neodpovídá.")
    return result.stdout


def parse_windows(text):
    result = []
    for line in text.splitlines():
        parts = line.split(None, 5)
        if len(parts) < 5 or not re.fullmatch(r"0x[0-9a-fA-F]+", parts[0]):
            continue
        try:
            pid = int(parts[2])
        except ValueError:
            continue
        result.append({"id": parts[0], "pid": pid, "class": parts[3].casefold()})
    return result


def parse_process_args(data):
    args = [arg.decode("utf-8", "replace") for arg in data.split(b"\0") if arg]
    # Chromium rewrites argv into one printable process title on Debian.
    if len(args) == 1 and " " in args[0]:
        try:
            return shlex.split(args[0])
        except ValueError:
            return []
    return args


def process_args(pid):
    try:
        directory = Path("/proc") / str(int(pid))
        if directory.stat().st_uid != os.getuid():
            return []
        return parse_process_args((directory / "cmdline").read_bytes())
    except (OSError, ValueError):
        return []


def parent_pid(pid):
    try:
        # A process name may contain spaces and parentheses.
        data = (Path("/proc") / str(int(pid)) / "stat").read_text()
        return int(data[data.rfind(")") + 2:].split()[1])
    except (OSError, ValueError, IndexError):
        return 0


def descends_from(pid, root_pid):
    if root_pid <= 0:
        return False
    seen = set()
    for _ in range(32):
        if pid == root_pid:
            return True
        if pid <= 1 or pid in seen:
            return False
        seen.add(pid)
        pid = parent_pid(pid)
    return False


def option(args, name):
    for index, value in enumerate(args):
        if value.startswith(name + "="):
            parts = [value[len(name) + 1:]]
            # Rewritten process titles can omit quotes around a profile path.
            for following in args[index + 1:]:
                if following.startswith("--"):
                    break
                parts.append(following)
            return " ".join(parts)
        if value == name and index + 1 < len(args):
            return args[index + 1]
    return None


def matches(window, request):
    pid = window["pid"]
    args = process_args(pid) if pid > 0 else []
    key = request["key"]
    command = request.get("command", [])
    profile = option(command, "--user-data-dir")
    if profile:
        return option(args, "--user-data-dir") == profile
    if key == "android-shell":
        return option(args, "--socket") == "padtv-android"
    classes = window["class"].split(".")
    if key == "files" and "thunar" in classes:
        return True
    if key == "kodi" and "kodi" in classes:
        return True
    if key == "browser" and "chromium" in classes:
        return bool(args) and option(args, "--user-data-dir") is None and option(args, "--app") is None
    return descends_from(pid, int(request.get("pid", 0)))


def find_window(windows, request):
    # wmctrl -S lists bottom to top. Prefer the app's most recently used window.
    return next((window for window in reversed(windows) if matches(window, request)), None)


def activate(request):
    from .session import wayland, app_id
    deadline = time.monotonic() + min(15, max(0, float(request.get("wait", 0))))
    command = request.get('command', [])
    chromium = bool(command) and Path(command[0]).name == 'chromium'
    if wayland() and not chromium:
        identity = app_id(request['key'], request.get('command', []))
        if not identity:
            return {'found': False}
        # Weston 14's nested Wayland backend does not export an app_id.
        # This fixed compositor title is never used to identify web apps.
        matcher = ('title:Weston Compositor - wayland-fullscreen'
                   if request['key'] == 'android-shell' else 'app_id:' + identity)
        while True:
            found = subprocess.run(['wlrctl', 'toplevel', 'find', matcher],
                                   capture_output=True, timeout=3)
            if found.returncode == 0:
                run('wlrctl', 'toplevel', 'focus', matcher)
                return {'found': True, 'window': identity}
            if found.returncode not in (0, 1):
                raise RuntimeError('Kompozitor neodpovídá.')
            if time.monotonic() >= deadline:
                return {'found': False}
            time.sleep(.2)
    while True:
        window = find_window(parse_windows(run("wmctrl", "-lpxS")), request)
        if window:
            # Openbox restores iconified windows as part of EWMH activation.
            run("wmctrl", "-ia", window["id"])
            return {"found": True, "window": window["id"]}
        if time.monotonic() >= deadline:
            return {"found": False}
        time.sleep(0.2)


def main():
    try:
        if not sys.platform.startswith("linux"):
            raise RuntimeError("Přepínání aplikací je dostupné v systému PadTV.")
        print(json.dumps({"ok": True, **activate(json.loads(sys.stdin.readline()))}), flush=True)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"ok": False, "error": str(error)}), flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
