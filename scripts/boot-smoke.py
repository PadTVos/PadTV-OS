#!/usr/bin/env python3
"""Boot an ISO without any hard disk and capture its screen via QEMU QMP.

This captures evidence for visual inspection; it does not infer boot success.
Requires qemu-system-x86_64; UEFI additionally requires the Debian ovmf package.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time


def response(stream):
    while True:
        raw = stream.readline()
        if not raw:
            raise RuntimeError("QEMU closed the monitor connection")
        message = json.loads(raw)
        if "return" in message or "error" in message or "QMP" in message:
            if "error" in message:
                raise RuntimeError(str(message["error"]))
            return message


def command(stream, name, arguments=None):
    payload = {"execute": name}
    if arguments:
        payload["arguments"] = arguments
    stream.write((json.dumps(payload) + "\n").encode())
    stream.flush()
    return response(stream)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("iso", type=Path)
    parser.add_argument("output", type=Path, help="Screen capture (.ppm)")
    parser.add_argument("--uefi", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=90)
    parser.add_argument("--key", choices=("ret", "esc", "up", "down", "left", "right"),
                        help="Send a remote key after boot, then wait 15 seconds before capture")
    args = parser.parse_args()
    if not args.iso.is_file():
        parser.error("ISO does not exist")
    if args.wait_seconds < 1:
        parser.error("wait-seconds must be positive")
    executable = shutil.which("qemu-system-x86_64")
    if not executable:
        parser.error("Install qemu-system-x86 first")
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="padtv-qemu-") as temp:
        scratch = Path(temp)
        monitor = scratch / "qmp.sock"
        argv = [executable, "-m", "4096", "-smp", "2", "-vga", "std", "-display", "none",
                "-nic", "none", "-boot", "d", "-cdrom", str(args.iso.resolve()),
                "-qmp", f"unix:{monitor},server=on,wait=off", "-monitor", "none",
                "-serial", "none", "-no-reboot"]
        if os.access("/dev/kvm", os.R_OK | os.W_OK):
            argv += ["-accel", "kvm", "-cpu", "host"]
        if args.uefi:
            code = Path("/usr/share/OVMF/OVMF_CODE_4M.fd")
            variables = Path("/usr/share/OVMF/OVMF_VARS_4M.fd")
            if not code.is_file() or not variables.is_file():
                parser.error("Install ovmf first")
            shutil.copyfile(variables, scratch / "vars.fd")
            argv += ["-drive", f"if=pflash,format=raw,readonly=on,file={code}",
                     "-drive", f"if=pflash,format=raw,file={scratch / 'vars.fd'}"]
        with output.with_suffix(".log").open("wb") as log:
            process = subprocess.Popen(argv, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 15
                while not monitor.exists():
                    if process.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError(f"QEMU failed to start; see {output.with_suffix('.log')}")
                    time.sleep(0.1)
                with socket.socket(socket.AF_UNIX) as connection:
                    connection.settimeout(10)
                    connection.connect(str(monitor))
                    with connection.makefile("rwb") as stream:
                        response(stream)
                        command(stream, "qmp_capabilities")
                        print("VM started; waiting for the live session...", flush=True)
                        deadline = time.monotonic() + args.wait_seconds
                        while time.monotonic() < deadline:
                            if process.poll() is not None:
                                raise RuntimeError("QEMU exited before capture")
                            time.sleep(0.5)
                        if args.key:
                            command(stream, "screendump", {"filename": str(output.with_suffix(".boot.ppm"))})
                            command(stream, "send-key", {"keys": [{"type": "qcode", "data": args.key}]})
                            time.sleep(15)
                        command(stream, "screendump", {"filename": str(output)})
                        command(stream, "quit")
                process.wait(timeout=10)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
    print(f"Captured {output}; inspect the image to determine boot success.")


if __name__ == "__main__":
    main()
