import json
from pathlib import Path
from urllib.parse import urlsplit
import jsonschema
root=Path(__file__).resolve().parent.parent
catalog=json.loads((root/'catalog/apps.json').read_text(encoding='utf-8'))
schema=json.loads((root/'catalog/schema.json').read_text(encoding='utf-8'))
jsonschema.Draft202012Validator(schema).validate(catalog)
assert len({a['id'] for a in catalog['apps']})==len(catalog['apps']), 'Duplicate app ID'
for app in catalog['apps']:
    if app['kind']=='web':
        url=urlsplit(app['target'])
        assert url.scheme=='https' and url.hostname and not url.username and not url.password
    if app['source'] in ('web','flathub'):
        assert app['kind']=={'web':'web','flathub':'flatpak'}[app['source']]
print(f"Validated {len(catalog['apps'])} apps")
