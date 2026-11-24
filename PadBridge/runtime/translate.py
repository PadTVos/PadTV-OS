"""Strict Apache-2.0 Enjarify adapter. Never publish a partially translated JAR."""
import resource
import sys
import zipfile
from enjarify import main
from enjarify.jvm.optimization import options

resource.setrlimit(resource.RLIMIT_AS, (1536 * 1024**2, 1536 * 1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (256 * 1024**2, 256 * 1024**2))
resource.setrlimit(resource.RLIMIT_CPU, (80, 85))
classes, errors = {}, []
with zipfile.ZipFile(sys.argv[1]) as source:
    names = sorted(n for n in source.namelist() if n.endswith('.dex') and '/' not in n)
    if not names:
        raise ValueError('No DEX files')
    for name in names:
        if source.getinfo(name).file_size > 64 * 1024**2:
            raise ValueError('DEX exceeds limit')
        before = set(classes)
        translated, failed = main.translate(source.read(name), options.PRETTY, allowErrors=False)
        if failed or before.intersection(translated):
            raise ValueError('Failed or duplicate class')
        classes.update(translated)
with zipfile.ZipFile(sys.argv[2], 'x', compression=zipfile.ZIP_DEFLATED) as output:
    for name, bytecode in sorted(classes.items()):
        if name.startswith(('android/', 'org/padtv/bridge/', 'java/', 'javax/', 'sun/', 'jdk/')):
            raise ValueError('APK tries to replace a host framework class')
        output.writestr(name, bytecode)
