"""Launch the Windows QEMU VM for PadTV without exposing host disks or a network monitor."""

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
MACHINE = ROOT / "virtual-machines" / "PadTV-0.3-System-Core"
DEFAULTS = {"name": "PadTV 0.4 Android Compatibility", "memory_mb": 16384, "cpus": 4,
            "iso": "dist/padtv-0.4.0-amd64.iso", "disk_gb": 64, "persistent": True}


def qemu_path():
    candidates = [shutil.which("qemu-system-x86_64")]
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if base:
            candidates.append(str(Path(base) / "qemu" / "qemu-system-x86_64.exe"))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    raise RuntimeError("Chybí QEMU pro Windows. Nainstalujte jej a spusťte PadTV znovu.")


def prepare():
    if sys.platform != "win32":
        raise RuntimeError("Tento spouštěč je určený pro Windows.")
    qemu = qemu_path()
    MACHINE.mkdir(parents=True, exist_ok=True)
    settings = MACHINE / "machine.json"
    if not settings.exists():
        settings.write_text(json.dumps(DEFAULTS, ensure_ascii=False, indent=2), encoding="utf-8")
    config = json.loads(settings.read_text(encoding="utf-8"))
    if not isinstance(config["memory_mb"], int) or not 2048 <= config["memory_mb"] <= 65536:
        raise ValueError("Paměť virtuálního stroje musí být mezi 2048 a 65536 MB.")
    if not isinstance(config["cpus"], int) or not 1 <= config["cpus"] <= 16:
        raise ValueError("Počet virtuálních jader musí být mezi 1 a 16.")
    iso = (ROOT / config["iso"]).resolve()
    if not iso.is_file():
        raise RuntimeError(f"Chybí ISO: {iso}")
    disk = MACHINE / "padtv.qcow2"
    if not disk.exists():
        if config.get("persistent", False):
            template = ROOT / "dist" / "padtv-persistence-v2-64G.qcow2"
            if not template.is_file():
                raise RuntimeError("Chybí šablona trvalého úložiště. Na Linuxu spusťte bash scripts/build-persistence.sh.")
            # Never replace an existing disk: it may contain installed apps/data.
            pending = MACHINE / "padtv.qcow2.partial"
            shutil.copyfile(template, pending)
            pending.rename(disk)
            return qemu, config, iso, disk
        size = config["disk_gb"]
        if not isinstance(size, int) or not 16 <= size <= 256:
            raise ValueError("Virtuální disk musí mít kapacitu 16 až 256 GB.")
        result = subprocess.run([str(qemu.with_name("qemu-img.exe")), "create", "-f", "qcow2", str(disk), f"{size}G"],
                                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "Virtuální disk se nepodařilo vytvořit.")
    return qemu, config, iso, disk


def focus_existing(maximize=False):
    try:
        pid = json.loads((MACHINE / "running.json").read_text(encoding="utf-8"))["pid"]
    except (OSError, ValueError, KeyError):
        return
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]

    found = False
    @callback_type
    def visit(handle, _):
        nonlocal found
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(handle, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(handle):
            found = True
            if maximize:
                user32.ShowWindow(handle, 3)
            elif user32.IsIconic(handle):
                user32.ShowWindow(handle, 9)
            user32.SetForegroundWindow(handle)
            return False
        return True
    user32.EnumWindows(visit, 0)
    return found


def launch():
    import msvcrt
    MACHINE.mkdir(parents=True, exist_ok=True)
    with (MACHINE / "run.lock").open("a+b") as lock:
        lock.seek(0, 2)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            focus_existing()
            return
        try:
            qemu, config, iso, disk = prepare()
            # HPET caused severe stalls with this Windows/WHPX host. Retain the
            # default interrupt controller and all configured CPU cores.
            # S3 resets VirtIO GPU resources; VM sleep uses s2idle instead.
            argv = [str(qemu), "-name", config["name"], "-machine", "q35,hpet=off", "-accel", "whpx",
                    "-global", "ICH9-LPC.disable_s3=1", "-global", "ICH9-LPC.disable_s4=1",
                    "-cpu", "max", "-m", str(config["memory_mb"]), "-smp", str(config["cpus"]),
                    "-vga", "none", "-device", "virtio-vga,xres=1600,yres=900",
                    "-display", "gtk,zoom-to-fit=on,gl=off,grab-on-hover=on,window-close=off",
                    "-drive", f"file={disk.as_posix().replace(',', ',,')},format=qcow2,if=virtio",
                    "-cdrom", str(iso), "-boot", "order=d,menu=on",
                    "-nic", "user,model=virtio-net-pci",
                    "-object", "rng-builtin,id=padtv-rng", "-device", "virtio-rng-pci,rng=padtv-rng",
                    "-device", "qemu-xhci,id=usb", "-device", "usb-tablet,bus=usb.0",
                    "-audiodev", "dsound,id=sound", "-device", "ich9-intel-hda",
                    "-device", "hda-output,audiodev=sound", "-rtc", "base=utc",
                    "-monitor", "none", "-serial", "none"]
            with (MACHINE / "qemu.log").open("ab") as log:
                log.write(f"\nPadTV start {datetime.now(timezone.utc).isoformat()}\n".encode())
                log.flush()
                process = subprocess.Popen(argv, cwd=MACHINE, stdout=log, stderr=log,
                                           creationflags=subprocess.CREATE_NO_WINDOW)
                (MACHINE / "running.json").write_text(json.dumps({"pid": process.pid}, indent=2), encoding="utf-8")
                for _ in range(50):
                    if process.poll() is not None or focus_existing(maximize=True):
                        break
                    time.sleep(0.2)
                code = process.wait()
            (MACHINE / "running.json").unlink(missing_ok=True)
            if code:
                detail = (MACHINE / "qemu.log").read_text(encoding="utf-8", errors="replace")[-1400:]
                raise RuntimeError(f"Virtuální stroj skončil chybou {code}.\n\n{detail}")
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true", help="Jen připravit konfiguraci a virtuální úložiště")
    args = parser.parse_args()
    try:
        if args.prepare:
            prepare()
            print(f"Virtuální stroj připraven: {MACHINE}")
        else:
            launch()
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        if sys.stderr is None:
            ctypes.windll.user32.MessageBoxW(None, str(error), "PadTV – virtuální počítač", 0x10)
        else:
            print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
