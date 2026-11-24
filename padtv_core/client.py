"""Small client, importable without dbus on Windows for development and tests."""
import argparse
import json
import sys


def call(method, *args):
    if not sys.platform.startswith('linux'):
        raise RuntimeError('Systémové API je dostupné pouze ve spuštěném PadTV.')
    import dbus
    obj = dbus.SystemBus().get_object('org.padtv.System1', '/org/padtv/System1')
    return json.loads(getattr(dbus.Interface(obj, 'org.padtv.System1'), method)(*args, timeout=30))


def main():
    parser = argparse.ArgumentParser(description='PadTV System API v1')
    parser.add_argument('command', choices=('info', 'devices', 'services', 'power', 'service'))
    parser.add_argument('arguments', nargs='*')
    args = parser.parse_args()
    methods = {'info': ('GetInfo', 0), 'devices': ('GetDevices', 0), 'services': ('GetServices', 0),
               'power': ('Power', 1), 'service': ('ServiceAction', 2)}
    method, count = methods[args.command]
    if len(args.arguments) != count:
        parser.error(f'Počet argumentů: {count}')
    try:
        print(json.dumps({'ok': True, 'data': call(method, *args.arguments)}, ensure_ascii=False))
        return 0
    except Exception as error:
        print(json.dumps({'ok': False, 'error': str(error)[:500]}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
