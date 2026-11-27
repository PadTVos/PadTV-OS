"""Pinned AOSP Linux host ART integration. No Android system image or emulator.

The upstream binary bundle is fetched by the user, not republished by PadTV.
Every activation requires a real sandboxed JNI + original DEX execution probe.
"""
import argparse, contextlib, hashlib, json, os, platform, shutil, subprocess
import sys, tarfile, tempfile, urllib.request, zipfile
from pathlib import Path, PurePosixPath

SOURCE = {
    'upstream': 'AOSP ART 16 Linux host test build distributed by the R8 project',
    'metadata_commit': 'f8ff923130e5da6265c9e246ba0be5b7acd2396d',
    'url': 'https://storage.googleapis.com/r8-deps/28e853aaa247b3dd4435df1a339e2b11e4488105',
    'sha256': '375302f225cfd66c066b243fcda3fe8535693ccbb205937e3d8a858a1b9ab713',
    'bytes': 591238194,
    'build_instructions': 'https://r8.googlesource.com/r8/+/f8ff923130e5da6265c9e246ba0be5b7acd2396d/tools/linux/README.art-versions',
}
MODULES = [('com.android.art', n) for n in ['core-oj', 'core-libart', 'okhttp', 'bouncycastle', 'apache-xml']] + [('com.android.i18n', 'core-icu4j'), ('com.android.conscrypt', 'conscrypt')]
BOOT = [f'/art/apex/{module}/javalib/{name}.jar' for module, name in MODULES]
ENV = {'ANDROID_ROOT':'/art', 'ANDROID_ART_ROOT':'/art/apex/com.android.art',
       'ANDROID_I18N_ROOT':'/art/com.android.i18n', 'ANDROID_TZDATA_ROOT':'/art/com.android.tzdata',
       'ANDROID_DATA':'/data', 'LD_LIBRARY_PATH':'/art/lib64:/native', 'HOME':'/data',
       'LANG':'C.UTF-8', 'PATH':'/usr/bin:/bin'}

def digest(path):
    sha = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024 * 1024): sha.update(block)
    return sha.hexdigest()

def default_root():
    return Path(os.environ.get('PADBRIDGE_ART_ROOT', str(Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share')))/'padbridge-runtimes/art-16.0.0'))).absolute()

def vm_options():
    boot = ':'.join(BOOT)
    return ['-Xbootclasspath:'+boot, '-Xbootclasspath-locations:'+boot,
            '-Ximage:/boot/boot.art', '-Xnoimage-dex2oat', '-Xusejit:false',
            '-XjdwpProvider:none', '-Xcheck:jni', '-Xmx384m',
            '-Djava.library.path=/art/lib64:/runtime:/native:/usr/lib/x86_64-linux-gnu/jni']

def sandbox(root, data, runtime):
    command = ['/usr/bin/bwrap', '--die-with-parent', '--new-session', '--unshare-all',
               '--cap-drop', 'ALL', '--clearenv']
    for path in ['/usr','/lib','/lib64','/bin']:
        if Path(path).exists(): command += ['--ro-bind', path, path]
    command += ['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/etc',
                '--ro-bind',str(root),'/art','--ro-bind',str(runtime),'/runtime',
                '--bind',str(data),'/data']
    for key, value in ENV.items(): command += ['--setenv',key,value]
    return command

def execute(command, timeout):
    p = subprocess.run(command, capture_output=True, text=True, timeout=timeout, env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'})
    result = {'exit_code':p.returncode, 'stdout':p.stdout[-20000:], 'stderr':p.stderr[-20000:]}
    if p.returncode: raise RuntimeError(json.dumps(result))
    return result

def extract(archive, destination):
    """Only pinned, bounded host components; never extract device images or links."""
    if archive.stat().st_size != SOURCE['bytes'] or digest(archive) != SOURCE['sha256']:
        raise ValueError('AOSP host archive checksum/size mismatch')
    total = 0; seen = set()
    with tarfile.open(archive, 'r:gz') as source:
        for member in source:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts: raise ValueError('Unsafe ART archive member')
            if not path.parts or path.parts[0] != 'art-16.0.0': raise ValueError('Unexpected archive root')
            relative = PurePosixPath(*path.parts[1:])
            selected = bool(relative.parts) and (relative.parts[0] in ['lib64','apex','com.android.i18n','com.android.tzdata'] or str(relative) in ['bin/dalvikvm64','bin/dex2oat64','build_spec.xml'])
            if not selected or member.isdir(): continue
            if not member.isfile(): raise ValueError('Nonregular ART component: '+str(relative))
            if str(relative) in seen: raise ValueError('Duplicate ART component')
            seen.add(str(relative)); total += member.size
            if total > 512*1024**2 or len(seen)>2000: raise ValueError('ART expansion limit')
            target = destination/str(relative); target.parent.mkdir(parents=True,exist_ok=True)
            with source.extractfile(member) as incoming, target.open('xb') as output:
                shutil.copyfileobj(incoming,output)
            target.chmod(0o755 if relative.parts[0]=='bin' else 0o644)
    for required in ['bin/dalvikvm64','bin/dex2oat64','lib64/libart.so']+[p.removeprefix('/art/') for p in BOOT]:
        if not (destination/required).is_file(): raise ValueError('Missing matched ART component: '+required)

def verify(root):
    record = json.loads((root/'padbridge-art.json').read_text())
    if record['schema'] != 1 or record['source'] != SOURCE or record['jni_create_result'] != 0 or not record['original_dex_executed']:
        raise ValueError('ART activation proof is invalid')
    files = record['files']
    if not isinstance(files,dict) or not 10<len(files)<2000: raise ValueError('Invalid ART file manifest')
    for name, expected in files.items():
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts: raise ValueError('Invalid ART manifest path')
        file = root/name
        if file.is_symlink() or not file.is_file() or digest(file) != expected:
            raise ValueError('ART component integrity mismatch: '+name)
    return record

def setup(root, runtime, archive=None):
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise RuntimeError('ART backend requires x86-64 Linux')
    if root.exists(): return verify(root)
    root.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.art-setup-',dir=root.parent) as folder:
        temporary = Path(folder); stage = temporary/'runtime'; stage.mkdir()
        if archive is None:
            archive = temporary/'host.tar.gz'; size = 0
            with urllib.request.urlopen(SOURCE['url'],timeout=90) as response, archive.open('xb') as out:
                while block := response.read(1024*1024):
                    size += len(block)
                    if size>SOURCE['bytes']: raise ValueError('ART download exceeds pinned size')
                    out.write(block)
        extract(archive,stage)
        data = temporary/'data'; (data/'boot/x86_64').mkdir(parents=True)
        build = ['/art/bin/dex2oat64','--host','--instruction-set=x86_64','--instruction-set-variant=default','--compiler-filter=verify','--base=0x70000000','--image=/data/boot/x86_64/boot.art','--oat-file=/data/boot/x86_64/boot.oat','--runtime-arg','-Xms64m','--runtime-arg','-Xmx512m']
        for jar in BOOT: build += ['--dex-file='+jar,'--dex-location='+jar]
        image = execute(sandbox(stage,data,runtime)+['--']+build,180)
        shutil.move(str(data/'boot'),str(stage/'boot'))
        probe = execute(sandbox(stage,data,runtime)+['--ro-bind',str(stage/'boot'),'/boot','--','/runtime/art-vm-probe','org/padtv/artprobe/RuntimeProbe']+vm_options()+['-Djava.class.path=/runtime/art-probe.apk'],60)
        if '"JNI_CreateJavaVM_result":0' not in probe['stdout'] or '"original_main_completed":true' not in probe['stdout'] or 'ART_ORIGINAL_DEX_REFLECTION_THREADS_EXCEPTIONS_OK 40000' not in probe['stdout']:
            raise RuntimeError('ART did not complete the original DEX probe')
        record = {'schema':1,'source':SOURCE,'jni_create_result':0,'original_dex_executed':True,
                  'probe_apk_sha256':digest(runtime/'art-probe.apk'),'image':image,'probe':probe,
                  'files':{p.relative_to(stage).as_posix():digest(p) for p in sorted(stage.rglob('*')) if p.is_file()}}
        (stage/'padbridge-art.json').write_text(json.dumps(record,indent=2)+'\n')
        stage.rename(root)
    return record

def prepare(input_dir, output):
    from resources import write
    sources=[input_dir/'original.apk']+sorted((input_dir/'splits').glob('*.apk'))
    with contextlib.ExitStack() as stack:
        archives=[stack.enter_context(zipfile.ZipFile(path)) for path in sources]
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as target: write(archives,target)

def run(activity, package, mode):
    # Called only inside the common Rust launcher sandbox. Preserve its grants.
    os.environ.update(ENV)
    sources=['/runtime/framework-art.jar','/app/art-resources.jar','/app/original.apk']+[str(p) for p in sorted(Path('/app/splits').glob('*.apk'))]
    command=['/art/bin/dalvikvm64']+vm_options()+['-cp',':'.join(sources),'org.padtv.bridge.Host',activity,package,mode]
    os.execv(command[0],command)

def main():
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest='action',required=True)
    install=sub.add_parser('setup');install.add_argument('--root',type=Path,default=default_root());install.add_argument('--archive',type=Path);install.add_argument('--runtime',type=Path,default=Path(__file__).resolve().parent)
    check=sub.add_parser('verify');check.add_argument('root',type=Path)
    p=sub.add_parser('prepare');p.add_argument('input',type=Path);p.add_argument('output',type=Path)
    r=sub.add_parser('run');r.add_argument('activity');r.add_argument('package');r.add_argument('mode',choices=['headless','wayland'])
    args=parser.parse_args()
    if args.action=='setup': result=setup(args.root.absolute(),args.runtime.absolute(),args.archive);print(json.dumps({'ok':True,'root':str(args.root),'jni_create_result':result['jni_create_result'],'original_dex_executed':True}))
    elif args.action=='verify':verify(args.root);print(json.dumps({'ok':True}))
    elif args.action=='prepare':prepare(args.input,args.output)
    else:run(args.activity,args.package,args.mode)
if __name__=='__main__':
    try: main()
    except Exception as error: print(json.dumps({'ok':False,'error':str(error)}));sys.exit(1)
