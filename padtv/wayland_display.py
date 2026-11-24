"""wlroots output management with timed rollback and per-user persistence."""
import json
import os
from pathlib import Path
import select
import sys


def parse_outputs(text):
    result = []
    for output in json.loads(text):
        modes, current = [], ''
        for mode in output.get('modes', []):
            # wlr-randr JSON already converts the protocol's mHz to Hz.
            label = f"{mode['width']}x{mode['height']}@{mode['refresh']:.3f}Hz"
            if label not in modes:
                modes.append(label)
            if mode.get('current') and output.get('enabled'):
                current = label
        result.append({'name': output['name'], 'modes': modes, 'current': current})
    return result


def settings_path():
    return Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))/'padtv'/'display.json'


def save(output, mode):
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        settings = json.loads(path.read_text())
    except (OSError, ValueError):
        settings = {}
    settings[output] = mode
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(settings))
    temporary.replace(path)


def restore(run):
    path = settings_path()
    if not path.is_file():
        return
    settings = json.loads(path.read_text())
    for output in parse_outputs(run('wlr-randr', '--json')):
        mode = settings.get(output['name'])
        if mode in output['modes'] and output['current'] and mode != output['current']:
            run('wlr-randr', '--output', output['name'], '--mode', mode)


def dispatch(request, run, emit):
    outputs = parse_outputs(run('wlr-randr', '--json'))
    if request['action'] == 'display-set':
        name, mode = request['output'], request['mode']
        output = next((o for o in outputs if o['name'] == name), None)
        if not output or not output['current'] or mode not in output['modes']:
            raise ValueError('Toto rozlišení není na zapnuté obrazovce dostupné.')
        confirmed = False
        try:
            run('wlr-randr', '--output', name, '--mode', mode)
            emit({'event': 'display-confirm', 'seconds': 15})
            if select.select([sys.stdin], [], [], 15)[0]:
                confirmed = json.loads(sys.stdin.readline()).get('confirm') is True
        finally:
            if not confirmed:
                run('wlr-randr', '--output', name, '--mode', output['current'])
        if confirmed:
            save(name, mode)
        outputs = parse_outputs(run('wlr-randr', '--json'))
    return {'displays': outputs}
