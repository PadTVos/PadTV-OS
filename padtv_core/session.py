"""Authorize the dedicated TV account only while its local GUI is active.

User services live outside a login scope. After a compositor restart polkit's
session guess can point at a serial console; query the actual graphical login.
"""


def active_tv_session(bus):
    import dbus
    import pwd
    uid = pwd.getpwnam('padtv').pw_uid
    manager = dbus.Interface(bus.get_object('org.freedesktop.login1', '/org/freedesktop/login1'),
                             'org.freedesktop.login1.Manager')
    for _, session_uid, _, seat, path in manager.ListSessions():
        if int(session_uid) != uid or not str(seat):
            continue
        props = dbus.Interface(bus.get_object('org.freedesktop.login1', path),
                               'org.freedesktop.DBus.Properties').GetAll('org.freedesktop.login1.Session')
        if eligible(props):
            return True
    return False


def eligible(props):
    return (bool(props.get('Active')) and not bool(props.get('Remote', True))
            and props.get('Type') == 'wayland' and props.get('Class') == 'user'
            and props.get('Service') == 'greetd' and props.get('TTY') == 'tty7')


if __name__ == '__main__':
    import dbus
    try:
        print('yes' if active_tv_session(dbus.SystemBus()) else 'no')
    except Exception:
        print('no')
