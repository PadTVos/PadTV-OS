"""Only explicitly supported system services can be controlled through this API."""
SERVICES = {'network': 'NetworkManager.service', 'bluetooth': 'bluetooth.service',
            'android': 'waydroid-container.service'}
OPERATIONS = {'start': 'StartUnit', 'stop': 'StopUnit', 'restart': 'RestartUnit'}


def validate(name, operation):
    if name not in SERVICES or operation not in OPERATIONS:
        raise ValueError('Nepovolená služba nebo operace.')
    return SERVICES[name], OPERATIONS[operation]


def control(bus, name, operation):
    import dbus
    unit, method = validate(name, operation)
    manager = dbus.Interface(bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1'),
                             'org.freedesktop.systemd1.Manager')
    return {'job': str(getattr(manager, method)(unit, 'replace'))}


def status(bus):
    import dbus
    manager = dbus.Interface(bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1'),
                             'org.freedesktop.systemd1.Manager')
    rows = []
    for name, unit in SERVICES.items():
        try:
            obj = bus.get_object('org.freedesktop.systemd1', manager.GetUnit(unit))
            props = dbus.Interface(obj, 'org.freedesktop.DBus.Properties').GetAll('org.freedesktop.systemd1.Unit')
            rows.append({'id': name, 'unit': unit, 'state': str(props['ActiveState']),
                         'detail': str(props['SubState'])})
        except dbus.DBusException:
            rows.append({'id': name, 'unit': unit, 'state': 'unavailable', 'detail': ''})
    return rows

