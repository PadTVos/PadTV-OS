"""Export five reviewable local Git repositories using an explicit allowlist."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parent.parent

def files_under(path):
    if path.is_file(): return [path]
    return [p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.is_symlink()]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'repositories')
    parser.add_argument('--refresh',action='store_true',help='Refresh only an unmodified generated export')
    args=parser.parse_args()
    output=args.output.resolve()
    if output==ROOT or ROOT.is_relative_to(output):
        parser.error('Export must not overwrite the workspace or its parent')
    config=json.loads((ROOT/'github/repositories.json').read_text(encoding='utf-8'))
    mapping={}
    os_files={}
    for name in ('padtv','padtv_core','padtv_store','catalog','packaging','live','scripts','tests','docs','github','assets','README.md','requirements-dev.txt','.gitignore','.gitattributes'):
        for p in files_under(ROOT/name): os_files[p.relative_to(ROOT).as_posix()]=p
    mapping['PadTV-OS']=os_files
    mapping['PadTV-Store']={p.relative_to(ROOT).as_posix():p for p in files_under(ROOT/'padtv_store')}
    mapping['PadTV-Store'].update({'integration/store_ui.py':ROOT/'padtv/store_ui.py',
        'catalog/apps.json':ROOT/'catalog/apps.json','docs/architecture.md':ROOT/'docs/github-and-store.md'})
    mapping['PadTV-Apps']={'catalog/apps.json':ROOT/'catalog/apps.json','catalog/schema.json':ROOT/'catalog/schema.json',
                          'scripts/validate.py':ROOT/'github/validate-catalog.py',
                          '.github/workflows/validate.yml':ROOT/'github/catalog-ci.yml'}
    mapping['PadTV-Updates']={'scripts/release-manifest.py':ROOT/'scripts/release-manifest.py',
                             'docs/architecture.md':ROOT/'docs/system-core.md'}
    mapping['PadTV-Website']={p.relative_to(ROOT).as_posix():p for p in files_under(ROOT/'docs')}
    intros={
        'PadTV-Store':'Modulární poskytovatelé aplikací PadTV. Spusťte `python -m padtv_store.cli status`.\n\n'
            'Qt adaptér je v `integration/store_ui.py` a používá rozhraní hostitele PadTV OS. '
            'Katalog je při vydání převzatý z PadTV-Apps; živý systém nestahuje neověřený kód z GitHubu.\n',
        'PadTV-Apps':'Verzovaný katalog aplikací PadTV. Upravujte `catalog/apps.json`; '
            'spusťte `pip install jsonschema` a `python scripts/validate.py`. '
            'Nepřidávejte APK ani binární soubory cizích aplikací.\n',
        'PadTV-Updates':'Metadata systémových vydání PadTV.\n\n'
            '`python scripts/release-manifest.py obraz.iso --url https://SKUTECNY-HOST/vydani.iso --output release.json --sign-key FINGERPRINT`\n\n'
            'URL musí odkazovat na skutečně publikovaný soubor. Soukromé klíče zůstávají mimo Git. '
            'Automatický aktualizátor a rollback OS nejsou součástí 0.3. '
            'Žádné aktivní aktualizační kanály zatím nejsou zveřejněné.\n',
        'PadTV-Website':'Dokumentace PadTV 0.3 – System Core.\n\n'
            '- [Architektura](docs/system-core.md)\n- [Store a repozitáře](docs/github-and-store.md)\n'
            '- [Stav ověření](docs/validation.md)\n\n'
            'Doména a veřejný web dosud nejsou nasazené. Toto je zdrojová dokumentace pro další web.\n'}
    # Check every destination before writing any of them.
    for name in mapping:
        dest=output/name
        if dest.is_symlink() or (dest.exists() and not args.refresh):
            raise SystemExit(f'Export already exists or is a symlink: {dest}')
        if dest.exists():
            marker=dest/'.padtv-export.json'
            previous=json.loads(marker.read_text(encoding='utf-8'))
            for relative,expected in previous['files'].items():
                path=dest/relative
                if not path.is_file() or path.is_symlink() or digest(path)!=expected:
                    raise SystemExit(f'Export contains a local change; preserved: {path}')
    for repo in config['repositories']:
        name=repo['name']; dest=output/name
        dest.mkdir(parents=True,exist_ok=True)
        for relative,source in mapping[name].items():
            target=dest/relative
            if not target.resolve().is_relative_to(dest.resolve()): raise ValueError('Unsafe export path')
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
        if name in intros:
            (dest/'README.md').write_text('# '+name+'\n\n'+intros[name],encoding='utf-8')
            (dest/'.gitignore').write_text('__pycache__/\n.venv/\n*.iso\n*.qcow2\n*.key\n.padtv-export.json\n',encoding='utf-8')
        if name=='PadTV-OS':
            (dest/'.github/workflows').mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/'github/os-ci.yml',dest/'.github/workflows/validate.yml')
        owned={p.relative_to(dest).as_posix():digest(p) for p in dest.rglob('*')
               if p.is_file() and '.git' not in p.relative_to(dest).parts
               and '__pycache__' not in p.relative_to(dest).parts and p.name!='.padtv-export.json'}
        (dest/'.padtv-export.json').write_text(json.dumps({'repository':name,'visibility':'public',
            'remote_created':config.get('remote_status') == 'published','files':owned},indent=2)+'\n',encoding='utf-8')
        if not (dest/'.git').exists(): subprocess.run(['git','init','--initial-branch=main',str(dest)],check=True,capture_output=True)
        print(f'{name}: {len(owned)} files prepared')

if __name__=='__main__': main()
