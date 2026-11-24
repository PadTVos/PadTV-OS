"""Strict Apache-2.0 Enjarify adapter. Never publish a partially translated JAR."""
import resource
import sys
import zipfile
from pathlib import Path
from contextlib import ExitStack
import resources
from enjarify import main
from enjarify.jvm.optimization import options

resource.setrlimit(resource.RLIMIT_AS, (1536 * 1024**2, 1536 * 1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (256 * 1024**2, 256 * 1024**2))
resource.setrlimit(resource.RLIMIT_CPU, (80, 85))
classes, errors = {}, []
root = Path(sys.argv[1])
sources = [root/'original.apk', *sorted((root/'splits').glob('*.apk'))] if root.is_dir() else [root]
for path in sources:
 with zipfile.ZipFile(path) as source:
    names = sorted(n for n in source.namelist() if n.endswith('.dex') and '/' not in n)
    for name in names:
        if source.getinfo(name).file_size > 64 * 1024**2:
            raise ValueError('DEX exceeds limit')
        before = set(classes)
        data=source.read(name)
        # Header versions 037-040 retain this metadata structure. The actual
        # decoder must accept every instruction; never rewrite or omit opcodes.
        if data[4:7] not in (b'035',b'037',b'038',b'039',b'040'):
            raise ValueError('Unsupported DEX container version')
        translated, failed = main.translate(data, options.PRETTY, allowErrors=False)
        if failed or before.intersection(translated):
            raise ValueError('Failed or duplicate class')
        classes.update(translated)
if not classes: raise ValueError('No executable DEX classes')
with zipfile.ZipFile(Path(__file__).with_name('framework.jar')) as framework:
    host_classes=set(n for n in framework.namelist() if n.endswith('.class'))
with zipfile.ZipFile(sys.argv[2], 'x', compression=zipfile.ZIP_DEFLATED) as output:
    for name, bytecode in sorted(classes.items()):
        # Support libraries and SDK compatibility classes may live in android.*.
        # Allow original APK code only when it does not replace an actual host class.
        if name in host_classes or name.startswith(('org/padtv/bridge/', 'java/', 'javax/', 'sun/', 'jdk/')):
            raise ValueError('APK tries to replace a host framework class: '+name)
        output.writestr(name, bytecode)
    with ExitStack() as stack:
        resources.write([stack.enter_context(zipfile.ZipFile(p)) for p in sources],output)
