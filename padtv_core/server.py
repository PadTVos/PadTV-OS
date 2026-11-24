"""D-Bus API v1. No shell, arbitrary commands, paths or unit names are accepted."""
import json
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from . import devices, identity, power, services

NAME = 'org.padtv.System1'
PATH = '/org/padtv/System1'


class SystemAPI(dbus.service.Object):
    def __init__(self, bus):
        self.bus = bus
        self.name = dbus.service.BusName(NAME, bus)
        super().__init__(self.name, PATH)

    def authorize(self, sender, action):
        if not sender:
            raise dbus.exceptions.DBusException('Chybí identita volajícího.', name=NAME+'.AccessDenied')
        if self.bus.get_unix_user(sender) == 0:
            return
        authority = dbus.Interface(self.bus.get_object('org.freedesktop.PolicyKit1', '/org/freedesktop/PolicyKit1/Authority'),
                                   'org.freedesktop.PolicyKit1.Authority')
        subject = ('system-bus-name', {'name': dbus.String(sender, variant_level=1)})
        allowed, _, _ = authority.CheckAuthorization(subject, action, {}, dbus.UInt32(0), '')
        if not allowed:
            raise dbus.exceptions.DBusException('Tuto akci smí provést pouze aktivní místní relace PadTV.', name=NAME+'.AccessDenied')

    @dbus.service.method(NAME, in_signature='', out_signature='s')
    def GetInfo(self):
        return json.dumps({**identity.status(), 'power': power.capabilities(self.bus)})

    @dbus.service.method(NAME, in_signature='', out_signature='s')
    def GetDevices(self):
        return json.dumps(devices.status(self.bus))

    @dbus.service.method(NAME, in_signature='', out_signature='s')
    def GetServices(self):
        return json.dumps(services.status(self.bus))

    @dbus.service.method(NAME, in_signature='s', out_signature='s', sender_keyword='sender')
    def Power(self, action, sender=None):
        self.authorize(sender, 'org.padtv.system.power')
        return json.dumps(power.perform(self.bus, str(action)))

    @dbus.service.method(NAME, in_signature='ss', out_signature='s', sender_keyword='sender')
    def ServiceAction(self, name, operation, sender=None):
        self.authorize(sender, 'org.padtv.system.services')
        return json.dumps(services.control(self.bus, str(name), str(operation)))


def main():
    DBusGMainLoop(set_as_default=True)
    api = SystemAPI(dbus.SystemBus())
    GLib.MainLoop().run()


if __name__ == '__main__':
    main()

