METHODS = {'poweroff': ('CanPowerOff', 'PowerOff'), 'reboot': ('CanReboot', 'Reboot'),
           'suspend': ('CanSuspend', 'Suspend')}


def manager(bus):
    import dbus
    return dbus.Interface(bus.get_object('org.freedesktop.login1', '/org/freedesktop/login1'),
                          'org.freedesktop.login1.Manager')


def capabilities(bus):
    instance = manager(bus)
    return {name: str(getattr(instance, methods[0])()) for name, methods in METHODS.items()}


def perform(bus, action):
    if action not in METHODS:
        raise ValueError('Neznámá akce napájení.')
    instance = manager(bus)
    check, method = METHODS[action]
    if str(getattr(instance, check)()) != 'yes':
        raise RuntimeError('Toto zařízení nyní nepodporuje požadovaný režim napájení.')
    # logind coordinates inhibitors and resumes existing user applications.
    getattr(instance, method)(False)
    return {'accepted': True, 'action': action}

