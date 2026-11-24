"""Waydroid integration. CLI operations return JSON and never invoke a shell."""

import argparse
from configparser import ConfigParser, Error as ConfigError
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from .apps import PACKAGE


class AndroidError(RuntimeError):
    pass


def run(command, timeout=30, check=True):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                env={**os.environ, "LC_ALL": "C", "WAYLAND_DISPLAY": "padtv-android"})
    except (OSError, subprocess.TimeoutExpired) as error:
        raise AndroidError(str(error)) from error
    reported_failure = command[0] == "waydroid" and any(message in (result.stderr + result.stdout).lower() for message in (
        "failed to access iplatform", "session is stopped", "failed to uninstall package",
        "failed with code:", "sending reply failed", "service manager never appeared"
    ))
    if check and (result.returncode or reported_failure):
        detail = (result.stderr or result.stdout).strip()[-1200:]
        raise AndroidError(detail or f"Příkaz skončil chybou {result.returncode}.")
    return result


def parse_apps(text):
    apps, current = [], {}
    for line in text.splitlines() + ["Name: "]:
        stripped = line.strip()
        if stripped.startswith("Name:"):
            if PACKAGE.fullmatch(current.get("package", "")):
                apps.append(current)
            current = {"name": stripped.partition(":")[2].strip()}
        elif stripped.startswith("packageName:"):
            current["package"] = stripped.partition(":")[2].strip()
    return apps


def status():
    available = sys.platform.startswith("linux") and bool(shutil.which("waydroid"))
    initialized = available and Path("/var/lib/waydroid/waydroid.cfg").is_file()
    result = {"available": available, "initialized": initialized, "running": False, "google_play": False}
    if initialized:
        config = ConfigParser()
        config.read('/var/lib/waydroid/waydroid.cfg')
        result['google_play'] = config.get('waydroid', 'system_ota', fallback='').endswith('/GAPPS.json')
        output = run(["waydroid", "status"], timeout=8, check=False).stdout
        result["running"] = bool(re.search(r"Session:\s*RUNNING", output))
    return result


def inventory():
    state = status()
    result = {**state, 'packages': [], 'known': False}
    # Browsing the Store must not boot a multi-GB Android container.
    if state['running'] and run(['waydroid', 'prop', 'get', 'sys.boot_completed'], timeout=8).stdout.strip() == '1':
        result.update(packages=[app['package'] for app in app_list()], known=True)
    return result


def require_initialized():
    state = status()
    if not state["available"]:
        raise AndroidError("Waydroid není nainstalovaný. Použijte sestavení PadTV s podporou Androidu.")
    if not state["initialized"]:
        raise AndroidError("Nejprve zvolte Připravit Android. Příprava stáhne obraz Androidu.")


def ensure_session():
    require_initialized()
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    if not runtime.is_dir() or runtime.stat().st_uid != os.getuid():
        raise AndroidError("Chybí uživatelská grafická relace.")
    if not (os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY")):
        raise AndroidError("Spusťte Android z grafické relace PadTV.")
    run(["systemctl", "--user", "start", "padtv-android-compositor.service"], timeout=20)
    wayland = runtime / "padtv-android"
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if wayland.exists() and wayland.is_socket():
            break
        time.sleep(0.15)
    else:
        raise AndroidError("Nepodařilo se spustit grafické prostředí Androidu.")
    run(["systemctl", "--user", "start", "padtv-android-session.service"], timeout=20)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if status()["running"]:
            # RUNNING only means the container/session exists. Before Android
            # finishes booting its app list can be empty even with installed APKs.
            try:
                if run(["waydroid", "prop", "get", "sys.boot_completed"], timeout=10).stdout.strip() == "1":
                    return
            except AndroidError:
                pass
        time.sleep(1)
    raise AndroidError("Android se ještě nespustil. Zkontrolujte stav služby waydroid-container.")


def app_list():
    require_initialized()
    return parse_apps(run(["waydroid", "app", "list"]).stdout)


def validate_package(package):
    if not PACKAGE.fullmatch(package):
        raise AndroidError("Neplatný identifikátor Android aplikace.")
    return package


def wait_package(package, present, timeout=30):
    """Android's package installer commits asynchronously after the CLI returns."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if (package in {app["package"] for app in app_list()}) == present:
            return
        time.sleep(1)
    message = "Instalace se nepotvrdila v seznamu aplikací." if present else "Odinstalování se nepotvrdilo. Aplikace zůstává nainstalovaná."
    raise AndroidError(message)


def apk_info(path):
    path = Path(path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() != ".apk":
        raise AndroidError("Vyberte existující soubor APK.")
    output = run(["aapt", "dump", "badging", str(path)], timeout=20).stdout
    package = re.search(r"^package: name='([^']+)'", output, re.MULTILINE)
    title = re.search(r"^application-label:'([^']*)'", output, re.MULTILINE)
    if not package:
        raise AndroidError("Soubor neobsahuje platný Android balíček.")
    name = validate_package(package[1])
    native = re.search(r"^native-code:(.+)$", output, re.MULTILINE)
    if native and not any(abi in native[1] for abi in ("'x86'", "'x86_64'")):
        raise AndroidError("Toto APK obsahuje jen ARM knihovny. PadTV pro PC potřebuje x86/x86_64 nebo univerzální APK.")
    return {"package": name, "name": title[1] if title and title[1] else name, "path": str(path)}


def execute(action, argument=None):
    if action not in ("status", "inventory", "inspect", "prepare", "prepare-play", "play", "list", "launch", "remove", "install", "open"):
        raise AndroidError("Neznámá operace.")
    if action == "status":
        return status()
    if action == 'inventory':
        return inventory()
    if action == "inspect":
        return apk_info(argument)
    if action in ("prepare", "prepare-play"):
        if not sys.platform.startswith("linux"):
            raise AndroidError("Android je dostupný v systému PadTV na Linuxu.")
        current = status()
        if current['initialized'] and (action == 'prepare' or current['google_play']):
            return current
        run(['systemctl', '--user', 'stop', 'padtv-android-session.service', 'padtv-android-compositor.service'], timeout=30)
        run(["pkexec", "/usr/lib/padtv/padtv-android-init", 'GAPPS' if action == 'prepare-play' else 'VANILLA'], timeout=1800)
        return status()
    if action == "list":
        ensure_session()
        return {"apps": app_list()}
    if action in ("launch", "remove", "play"):
        validate_package(argument)
    if action == "install":
        info = apk_info(argument)
    ensure_session()
    if action == 'play':
        if 'com.android.vending' not in {app['package'] for app in app_list()}:
            raise AndroidError('Google Play není připravený. V detailu aplikace zvolte Připravit Google Play.')
        run(['waydroid', 'app', 'intent', 'android.intent.action.VIEW', f'market://details?id={argument}'], timeout=90)
        run(['waydroid', 'show-full-ui'], timeout=90)
        # This opens the official store, not a completed installation.
        return {'opened': True, 'installed': False, 'package': argument}
    if action == "open":
        run(["waydroid", "show-full-ui"], timeout=90)
        return {"opened": True}
    if action == "launch":
        run(["waydroid", "app", "launch", argument], timeout=90)
        return {"launched": argument}
    if action == "install":
        # Standard user app installation into /data/app, never /system/app.
        run(["waydroid", "app", "install", info["path"]], timeout=180)
        wait_package(info["package"], present=True)
        return info
    if action == "remove":
        confirmation_timeout = 30
        try:
            run(["waydroid", "app", "remove", argument], timeout=90)
        except AndroidError:
            # Some Android 13 images reject Waydroid's uninstall PendingIntent.
            # Use Android's ordinary uninstall dialog, still as the user.
            run(["waydroid", "app", "intent", "android.intent.action.DELETE", f"package:{argument}"], timeout=90)
            run(["waydroid", "show-full-ui"], timeout=90)
            confirmation_timeout = 180
        wait_package(argument, present=False, timeout=confirmation_timeout)
        return {"removed": argument}
    raise AndroidError("Neznámá operace.")


def main():
    parser = argparse.ArgumentParser(description="PadTV Android runtime")
    parser.add_argument("action", choices=("status", "inventory", "prepare", "prepare-play", "play", "open", "list", "inspect", "install", "launch", "remove"))
    parser.add_argument("argument", nargs="?")
    args = parser.parse_args()
    if args.action in ("inspect", "install", "launch", "remove", "play") and not args.argument:
        parser.error("Tato operace vyžaduje argument.")
    try:
        print(json.dumps({"ok": True, **execute(args.action, args.argument)}, ensure_ascii=False))
        return 0
    except (AndroidError, OSError, ConfigError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
