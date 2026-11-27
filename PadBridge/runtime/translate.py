"""Strict Apache-2.0 Enjarify adapter. Never publish a partially translated JAR."""
import resource
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from contextlib import ExitStack
import resources
from enjarify import main
from enjarify.jvm.optimization import options
import dex_fixes
dex_fixes.install()

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
boot_classes=json.loads(Path(__file__).with_name('host-api.json').read_text())
with zipfile.ZipFile(sys.argv[2], 'x', compression=zipfile.ZIP_DEFLATED) as output:
    for name, bytecode in sorted(classes.items()):
        # Support libraries and SDK compatibility classes may live in android.*.
        # Allow original APK code only when it does not replace an actual host class.
        # Android and OpenJDK both use parent-first loading for boot classes.
        # Some original APKs bundle desugaring copies of java.util.function.
        # Keep their bytes in the JAR; the actual boot class wins at execution.
        boot_copy=name.endswith('.class') and name[:-6] in boot_classes
        if name in host_classes or name.startswith(('org/padtv/bridge/', 'sun/', 'jdk/')) or (name.startswith(('java/','javax/')) and not boot_copy):
            raise ValueError('APK tries to replace a host framework class: '+name)
        output.writestr(name, bytecode)
    with ExitStack() as stack:
        resources.write([stack.enter_context(zipfile.ZipFile(p)) for p in sources],output)
repaired=Path(sys.argv[2]+'.constructors')
subprocess.run(['/usr/bin/java','-Xmx512m','-Xss512k','-XX:ActiveProcessorCount=2','-XX:CompressedClassSpaceSize=64m','-XX:ReservedCodeCacheSize=32m','-XX:+UseSerialGC','-cp','/runtime/constructor-repair.jar:/usr/share/java/asm-all.jar','org.padtv.bridge.tools.ConstructorRepair',sys.argv[2],str(repaired)],check=True,timeout=30)
os.replace(repaired,sys.argv[2])
