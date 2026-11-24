def status(bus):
    import dbus
    result = {'network': [], 'bluetooth': [], 'errors': {}}
    try:
        manager = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager'),
                                 'org.freedesktop.NetworkManager')
        for path in manager.GetDevices():
            props = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', path),
                                   'org.freedesktop.DBus.Properties').GetAll('org.freedesktop.NetworkManager.Device')
            result['network'].append({'interface': str(props['Interface']), 'type': int(props['DeviceType']),
                                      'state': int(props['State'])})
    except dbus.DBusException:
        result['errors']['network'] = 'Síťová služba není dostupná.'
    try:
        objects = dbus.Interface(bus.get_object('org.bluez', '/'), 'org.freedesktop.DBus.ObjectManager').GetManagedObjects()
        for path, interfaces in objects.items():
            if 'org.bluez.Adapter1' in interfaces:
                props = interfaces['org.bluez.Adapter1']
                result['bluetooth'].append({'path': str(path), 'name': str(props.get('Alias', 'Bluetooth')),
                                            'powered': bool(props['Powered'])})
    except dbus.DBusException:
        result['errors']['bluetooth'] = 'Bluetooth služba není dostupná.'
    return result

