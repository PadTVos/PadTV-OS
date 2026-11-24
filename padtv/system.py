"""Unprivileged settings worker. Requests/secrets travel over stdin, never a shell.

Each process owns one operation; BlueZ discovery and pairing keep their D-Bus
connection alive. The Qt front end consumes newline-delimited JSON events.
"""
import getpass
import json
import os
from pathlib import Path
import re
import select
import subprocess
import sys
import tempfile
import time
import uuid

NM = "org.freedesktop.NetworkManager"
NP = "/org/freedesktop/NetworkManager"
PROPS = "org.freedesktop.DBus.Properties"


def emit(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)


def run(*args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=20,
                            env={**os.environ, "LC_ALL": "C"})
    if result.returncode:
        raise RuntimeError(result.stderr.strip()[:400] or "Služba příkaz odmítla.")
    return result.stdout.strip()


def props(bus, service, path, interface):
    import dbus
    return dbus.Interface(bus.get_object(service, path), PROPS).GetAll(interface)


def iface(bus, service, path, interface):
    import dbus
    return dbus.Interface(bus.get_object(service, path), interface)


def virtual_machine():
    result = subprocess.run(["systemd-detect-virt", "--vm"], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def wifi_security(ap):
    flags = int(ap.get("WpaFlags", 0)) | int(ap.get("RsnFlags", 0))
    if flags & (0x200 | 0x2000):
        return "enterprise"
    if flags & 0x100:
        return "wpa-psk"
    if flags & 0x400:
        return "sae"
    if flags & 0x800:
        return "owe"
    return "wep" if int(ap.get("Flags", 0)) & 1 else "open"


def network(bus, request):
    import dbus
    manager = iface(bus, NM, NP, NM)
    devices = manager.GetDevices()
    action = request["action"]
    saved = []
    for path in iface(bus, NM, NP + "/Settings", NM + ".Settings").ListConnections():
        connection = iface(bus, NM, path, NM + ".Settings.Connection")
        try:
            cfg = connection.GetSettings()
        except dbus.DBusException:
            continue
        meta = cfg.get("connection", {})
        if meta.get("type") == "802-11-wireless" and f"user:{getpass.getuser()}:" in meta.get("permissions", []):
            saved.append({"path": str(path), "name": str(meta.get("id", "Wi-Fi"))})
    if action == "network-forget":
        path = request["connection"]
        if path not in [s["path"] for s in saved]:
            raise ValueError("Toto připojení nepatří profilu PadTV nebo již neexistuje.")
        iface(bus, NM, path, NM + ".Settings.Connection").Delete()
        saved = [s for s in saved if s["path"] != path]
    if action == "wifi-power":
        iface(bus, NM, NP, PROPS).Set(NM, "WirelessEnabled", dbus.Boolean(request["enabled"]))
    elif action == "network-disconnect":
        path = request["device"]
        if path not in devices:
            raise ValueError("Síťový adaptér již není připojený.")
        iface(bus, NM, path, NM + ".Device").Disconnect()
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and int(props(bus, NM, path, NM + ".Device")["State"]) > 30:
            time.sleep(0.1)
    elif action == "network-connect":
        connect_network(bus, manager, devices, request)
    rows, access_points = [], []
    for device in devices:
        data = props(bus, NM, device, NM + ".Device")
        kind = int(data["DeviceType"])
        if kind not in (1, 2) or not data.get("Managed", True):
            continue
        addresses = []
        if data.get("Ip4Config", "/") != "/":
            ip = props(bus, NM, data["Ip4Config"], NM + ".IP4Config")
            addresses = [str(a["address"]) for a in ip.get("AddressData", [])]
        rows.append({"path": str(device), "name": str(data["Interface"]),
                     "type": kind, "connected": int(data["State"]) == 100,
                     "state": int(data["State"]), "addresses": addresses})
        if kind == 2:
            wireless = iface(bus, NM, device, NM + ".Device.Wireless")
            if action == "network-scan":
                previous_scan = int(props(bus, NM, device, NM + ".Device.Wireless").get("LastScan", -1))
                try:
                    wireless.RequestScan(dbus.Dictionary({}, signature="sv"))
                except dbus.DBusException as error:
                    if "NotAllowed" not in error.get_dbus_name():
                        raise
                # A scan is asynchronous and can span many radio channels.
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    if int(props(bus, NM, device, NM + ".Device.Wireless").get("LastScan", -1)) > previous_scan:
                        break
                    time.sleep(0.25)
            active = props(bus, NM, device, NM + ".Device.Wireless").get("ActiveAccessPoint", "/")
            for path in wireless.GetAccessPoints():
                ap = props(bus, NM, path, NM + ".AccessPoint")
                ssid = bytes(ap["Ssid"])
                if not ssid:
                    continue
                access_points.append({"path": str(path), "device": str(device),
                                      "name": ssid.decode("utf-8", "replace"),
                                      "strength": int(ap["Strength"]), "security": wifi_security(ap),
                                      "connected": path == active and int(data["State"]) == 100})
    state = props(bus, NM, NP, NM)
    return {"devices": rows, "aps": sorted(access_points, key=lambda a: (not a["connected"], -a["strength"])),
            "wifi": bool(state["WirelessEnabled"]), "hardware": bool(state["WirelessHardwareEnabled"]),
            "vm": virtual_machine(), "saved": saved}


def connect_network(bus, manager, devices, request):
    import dbus
    device = request["device"]
    if device not in devices:
        raise ValueError("Síťový adaptér již není připojený.")
    data = props(bus, NM, device, NM + ".Device")
    ap_path = request.get("ap", "/")
    if int(data["DeviceType"]) == 1:
        active = manager.ActivateConnection("/", device, "/")
    else:
        aps = iface(bus, NM, device, NM + ".Device.Wireless").GetAccessPoints()
        if ap_path not in aps:
            raise ValueError("Síť již není v dosahu. Obnovte seznam.")
        ap = props(bus, NM, ap_path, NM + ".AccessPoint")
        security = wifi_security(ap)
        if security in ("wep", "enterprise"):
            raise ValueError("Tato verze podporuje otevřené sítě a WPA2/WPA3 Personal. Podniková Wi-Fi a WEP vyžadují správce sítě.")
        ssid = bytes(ap["Ssid"])
        settings = {"connection": {"id": ssid.decode("utf-8", "replace"), "uuid": str(uuid.uuid4()),
                                   "type": "802-11-wireless", "autoconnect": True,
                                   "permissions": dbus.Array([f"user:{getpass.getuser()}:"], signature="s")},
                    "802-11-wireless": {"ssid": dbus.ByteArray(ssid), "mode": "infrastructure"},
                    "ipv4": {"method": "auto"}, "ipv6": {"method": "auto"}}
        password = request.get("password", "")
        if security in ("wpa-psk", "sae"):
            if not password:
                # Reuse a saved user connection without ever reading its secret.
                for saved in data.get("AvailableConnections", []):
                    cfg = iface(bus, NM, saved, NM + ".Settings.Connection").GetSettings()
                    if bytes(cfg.get("802-11-wireless", {}).get("ssid", b"")) == ssid:
                        active = manager.ActivateConnection(saved, device, ap_path)
                        break
                else:
                    raise ValueError("Zadejte heslo k této Wi-Fi síti.")
                wait_network(bus, active)
                return
            if security == "wpa-psk" and not (8 <= len(password) <= 63 or re.fullmatch(r"[0-9a-fA-F]{64}", password)):
                raise ValueError("Heslo WPA2 musí mít 8–63 znaků (nebo 64 hexadecimálních číslic).")
        if security != "open":
            settings["802-11-wireless-security"] = {"key-mgmt": security}
            if password:
                settings["802-11-wireless-security"].update({"psk": password, "psk-flags": dbus.UInt32(0)})
        # Update our saved profile instead of accumulating duplicates after a
        # mistyped password. Administrator-owned connections are left intact.
        for saved in data.get("AvailableConnections", []):
            connection = iface(bus, NM, saved, NM + ".Settings.Connection")
            cfg = connection.GetSettings()
            if (bytes(cfg.get("802-11-wireless", {}).get("ssid", b"")) == ssid and
                    f"user:{getpass.getuser()}:" in cfg.get("connection", {}).get("permissions", []) and
                    cfg.get("802-11-wireless-security", {}).get("key-mgmt", "open") == security):
                if security != "open":
                    cfg["802-11-wireless-security"] = dbus.Dictionary(settings["802-11-wireless-security"], signature="sv")
                connection.Update(cfg)
                active = manager.ActivateConnection(saved, device, ap_path)
                wait_network(bus, active)
                return
        typed = dbus.Dictionary({key: dbus.Dictionary(value, signature="sv") for key, value in settings.items()}, signature="sa{sv}")
        _, active = manager.AddAndActivateConnection(typed, device, ap_path)
    wait_network(bus, active)


def wait_network(bus, active):
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        state = int(props(bus, NM, active, NM + ".Connection.Active")["State"])
        if state == 2:
            return
        if state == 4:
            raise RuntimeError("Připojení se nezdařilo. Zkontrolujte heslo a dostupnost sítě.")
        time.sleep(0.5)
    iface(bus, NM, NP, NM).DeactivateConnection(active)
    raise RuntimeError("Síť neodpověděla včas. Zkontrolujte heslo a signál.")


def bluetooth(bus, request):
    import dbus
    if request["action"] == "bluetooth-status" and not list(Path("/sys/class/bluetooth").glob("hci*")):
        return {"adapters": [], "devices": []}
    objects = iface(bus, "org.bluez", "/", "org.freedesktop.DBus.ObjectManager")
    managed = objects.GetManagedObjects()
    adapters = [p for p, data in managed.items() if "org.bluez.Adapter1" in data]
    action = request["action"]
    if action != "bluetooth-status" and not adapters:
        raise RuntimeError("Bluetooth adaptér není připojený.")
    if action in ("bluetooth-power", "bluetooth-scan"):
        adapter = request.get("adapter", str(adapters[0]))
        if adapter not in adapters:
            raise ValueError("Adaptér již není dostupný.")
        if action == "bluetooth-power":
            iface(bus, "org.bluez", adapter, PROPS).Set("org.bluez.Adapter1", "Powered", dbus.Boolean(request["enabled"]))
        else:
            control = iface(bus, "org.bluez", adapter, "org.bluez.Adapter1")
            control.StartDiscovery()
            try:
                time.sleep(8)
            finally:
                control.StopDiscovery()
    elif action in ("bluetooth-connect", "bluetooth-disconnect", "bluetooth-forget"):
        path = request["device"]
        device = managed.get(path, {}).get("org.bluez.Device1")
        if device is None:
            raise ValueError("Zařízení již není dostupné.")
        control = iface(bus, "org.bluez", path, "org.bluez.Device1")
        if action == "bluetooth-forget":
            iface(bus, "org.bluez", device["Adapter"], "org.bluez.Adapter1").RemoveDevice(path)
        elif action == "bluetooth-disconnect":
            control.Disconnect()
        elif not device.get("Paired", False):
            from .bluetooth_agent import pair
            pair(bus, path)
        else:
            control.Connect(timeout=35)
    managed = objects.GetManagedObjects()
    return {"adapters": [{"path": str(p), "name": str(d["org.bluez.Adapter1"].get("Alias", "Bluetooth")),
                           "powered": bool(d["org.bluez.Adapter1"]["Powered"])}
                          for p, d in managed.items() if "org.bluez.Adapter1" in d],
            "devices": [{"path": str(p), "name": str(d["org.bluez.Device1"].get("Alias", "Zařízení")),
                         "paired": bool(d["org.bluez.Device1"].get("Paired", False)),
                         "connected": bool(d["org.bluez.Device1"].get("Connected", False))}
                        for p, d in managed.items() if "org.bluez.Device1" in d]}


def audio(request):
    sinks = json.loads(run("pactl", "--format=json", "list", "sinks"))
    action = request["action"]
    if action == "audio-output":
        name = request["sink"]
        if name not in [s["name"] for s in sinks]:
            raise ValueError("Zvukový výstup již není připojený.")
        run("pactl", "set-default-sink", name)
        for stream in json.loads(run("pactl", "--format=json", "list", "sink-inputs")):
            run("pactl", "move-sink-input", str(stream["index"]), name)
    elif action == "audio-volume":
        volume = int(request["volume"])
        if not 0 <= volume <= 100:
            raise ValueError("Hlasitost musí být 0–100 %.")
        run("wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SINK@", f"{volume}%")
    elif action == "audio-mute":
        run("wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle")
    default = run("pactl", "get-default-sink") if sinks else ""
    current = run("wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@") if sinks else "Volume: 0.00"
    def description(sink, index):
        name = sink.get("description")
        if name and name != "(null)":
            return name
        return "HDMI / DisplayPort" if "hdmi" in sink["name"] else f"Zvukový výstup {index + 1}"
    result = {"sinks": [{"name": s["name"], "description": description(s, i)} for i, s in enumerate(sinks)],
            "default": default, "volume": round(float(current.split()[1]) * 100), "mute": "MUTED" in current}
    if action != "audio-status":
        save_audio(result)
    return result


def audio_settings_path():
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "padtv" / "audio.json"


def save_audio(state):
    path = audio_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix="audio-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"sink": state["default"], "volume": state["volume"], "mute": state["mute"]}, stream)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def restore_audio():
    path = audio_settings_path()
    if not path.exists():
        return
    state = json.loads(path.read_text(encoding="utf-8"))
    if (type(state.get("volume")) is not int or not 0 <= state["volume"] <= 100 or
            type(state.get("mute")) is not bool or not isinstance(state.get("sink"), str)):
        raise ValueError("Uložené nastavení zvuku není platné.")
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            sinks = json.loads(run("pactl", "--format=json", "list", "sinks"))
            if not sinks:
                time.sleep(1)
                continue
            if state["sink"] in [s["name"] for s in sinks]:
                run("pactl", "set-default-sink", state["sink"])
            run("wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SINK@", f"{state['volume']}%")
            run("wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1" if state["mute"] else "0")
            return
        except (RuntimeError, subprocess.TimeoutExpired):
            time.sleep(1)
    raise RuntimeError("Zvukový server se při startu nepodařilo načíst.")


def parse_displays(text):
    displays, current = [], None
    for line in text.splitlines():
        match = re.match(r"^(\S+) connected\b", line)
        if match:
            current = {"name": match[1], "modes": [], "current": ""}
            displays.append(current)
        elif line and not line[0].isspace():
            current = None
        elif current is not None:
            match = re.match(r"\s+(\d+x\d+)\s+(.+)", line)
            if match:
                mode, rates = match.groups()
                current["modes"].append(mode)
                if "*" in rates:
                    current["current"] = mode
    return displays


def display(request):
    from .session import wayland
    if wayland():
        from .wayland_display import dispatch as wayland_display
        return wayland_display(request, run, emit)
    displays = parse_displays(run("xrandr", "--query"))
    if request["action"] == "display-set":
        output, mode = request["output"], request["mode"]
        entry = next((d for d in displays if d["name"] == output), None)
        if not entry or mode not in entry["modes"] or not entry["current"]:
            raise ValueError("Toto rozlišení není na zapnuté obrazovce dostupné.")
        confirmed = False
        try:
            run("xrandr", "--output", output, "--mode", mode)
            emit({"event": "display-confirm", "seconds": 15})
            if select.select([sys.stdin], [], [], 15)[0]:
                confirmed = json.loads(sys.stdin.readline()).get("confirm") is True
        finally:
            if not confirmed:
                run("xrandr", "--output", output, "--mode", entry["current"])
        displays = parse_displays(run("xrandr", "--query"))
    return {"displays": displays}


def dispatch(request):
    action = request["action"]
    if action == "system-status":
        from padtv_core.client import call
        return {**call('GetInfo'), 'services': call('GetServices')}
    if action == 'system-service':
        from padtv_core.client import call
        call('ServiceAction', request['service'], request['operation'])
        return {**call('GetInfo'), 'services': call('GetServices')}
    if action.startswith("audio-"):
        return audio(request)
    if action.startswith("display-"):
        return display(request)
    import dbus
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    if action.startswith(("network-", "wifi-")):
        return network(bus, request)
    if action.startswith("bluetooth-"):
        return bluetooth(bus, request)
    raise ValueError("Neznámé nastavení.")


def main():
    try:
        if not sys.platform.startswith("linux"):
            raise RuntimeError("Skutečná nastavení jsou dostupná po spuštění systému PadTV.")
        if sys.argv[1:] == ["--restore-audio"]:
            restore_audio()
            return 0
        if sys.argv[1:] == ['--restore-display']:
            from .wayland_display import restore
            restore(run)
            return 0
        if len(sys.argv) == 3 and sys.argv[1] == "--volume":
            if sys.argv[2] == "mute":
                audio({"action": "audio-mute"})
            elif sys.argv[2] in ("up", "down"):
                current = audio({"action": "audio-status"})["volume"]
                step = 5 if sys.argv[2] == "up" else -5
                audio({"action": "audio-volume", "volume": min(100, max(0, current + step))})
            else:
                raise ValueError("Neplatné ovládání hlasitosti.")
            return 0
        # The reader must not prefetch later interactive replies before select().
        request = json.loads(sys.stdin.readline())
        emit({"ok": True, "data": dispatch(request)})
    except Exception as error:
        # Never echo the request: it can contain a Wi-Fi password.
        message = str(error)
        if "org.freedesktop.DBus.Error.ServiceUnknown" in message:
            message = "Služba není dostupná. Zkuste restartovat PadTV."
        emit({"ok": False, "error": message[:500]})
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
