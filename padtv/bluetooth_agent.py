"""BlueZ agent scoped to the device the viewer chose to pair."""
import json
import sys

import dbus
import dbus.service
from gi.repository import GLib

from .system import emit, iface, PROPS

AGENT_PATH = "/org/padtv/agent"


class Rejected(dbus.DBusException):
    _dbus_error_name = "org.bluez.Error.Rejected"


class Agent(dbus.service.Object):
    def __init__(self, bus, device):
        super().__init__(bus, AGENT_PATH)
        self.device, self.pending = device, None

    def check(self, device):
        if device != self.device:
            raise Rejected("Jiné zařízení nebylo vybráno.")

    def ask(self, device, kind, reply, error, **data):
        self.check(device)
        self.cancel_pending()
        self.pending = (kind, reply, error)
        emit({"event": kind, **data})

    def cancel_pending(self):
        if self.pending:
            pending, self.pending = self.pending, None
            pending[2](Rejected("Párování bylo zrušeno."))

    def receive(self, answer):
        if not self.pending:
            return
        (kind, reply, error), self.pending = self.pending, None
        if not answer.get("confirm"):
            error(Rejected("Párování bylo zrušeno."))
        elif kind == "bluetooth-pin":
            pin = str(answer.get("value", ""))
            if not 1 <= len(pin) <= 16:
                error(Rejected("Neplatný PIN."))
            else:
                reply(pin)
        elif kind == "bluetooth-passkey":
            value = str(answer.get("value", ""))
            if not value.isascii() or not value.isdigit() or len(value) > 6:
                error(Rejected("Neplatný číselný kód."))
            else:
                reply(dbus.UInt32(int(value)))
        else:
            reply()

    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Release(self):
        self.cancel_pending()

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="s", async_callbacks=("reply", "error"))
    def RequestPinCode(self, device, reply, error):
        self.ask(device, "bluetooth-pin", reply, error)

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="u", async_callbacks=("reply", "error"))
    def RequestPasskey(self, device, reply, error):
        self.ask(device, "bluetooth-passkey", reply, error)

    @dbus.service.method("org.bluez.Agent1", in_signature="ou", out_signature="", async_callbacks=("reply", "error"))
    def RequestConfirmation(self, device, passkey, reply, error):
        self.ask(device, "bluetooth-confirm", reply, error, value=f"{int(passkey):06d}")

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="", async_callbacks=("reply", "error"))
    def RequestAuthorization(self, device, reply, error):
        self.ask(device, "bluetooth-confirm", reply, error, value="Povolit párování vybraného zařízení?")

    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def AuthorizeService(self, device, service):
        self.check(device)

    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        self.check(device)
        emit({"event": "bluetooth-display", "value": str(pincode)})

    @dbus.service.method("org.bluez.Agent1", in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        self.DisplayPinCode(device, f"{int(passkey):06d}")

    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Cancel(self):
        self.cancel_pending()
        emit({"event": "bluetooth-cancel"})


def pair(bus, device):
    agent = Agent(bus, device)
    manager = iface(bus, "org.bluez", "/org/bluez", "org.bluez.AgentManager1")
    control = iface(bus, "org.bluez", device, "org.bluez.Device1")
    loop, errors = GLib.MainLoop(), []

    def fail(error):
        errors.append(error)
        loop.quit()

    def receive(source, condition):
        line = sys.stdin.readline()
        if not line:
            agent.cancel_pending()
            control.CancelPairing(reply_handler=lambda: None, error_handler=lambda e: None)
            fail(RuntimeError("Párování bylo zrušeno."))
            return False
        try:
            agent.receive(json.loads(line))
        except (ValueError, TypeError):
            agent.cancel_pending()
        return True

    def timeout():
        agent.cancel_pending()
        control.CancelPairing(reply_handler=lambda: None, error_handler=lambda e: None)
        fail(RuntimeError("Párování vypršelo. Zkuste zařízení přepnout do režimu párování."))
        return False

    manager.RegisterAgent(AGENT_PATH, "KeyboardDisplay")
    watch = GLib.io_add_watch(sys.stdin, GLib.IO_IN | GLib.IO_HUP, receive)
    timer = GLib.timeout_add_seconds(100, timeout)
    try:
        control.Pair(reply_handler=loop.quit, error_handler=fail, timeout=100)
        loop.run()
        if errors:
            raise errors[0]
        iface(bus, "org.bluez", device, PROPS).Set("org.bluez.Device1", "Trusted", dbus.Boolean(True))
        control.Connect(timeout=35)
    finally:
        agent.cancel_pending()
        GLib.source_remove(watch)
        GLib.source_remove(timer)
        manager.UnregisterAgent(AGENT_PATH)
        agent.remove_from_connection()
