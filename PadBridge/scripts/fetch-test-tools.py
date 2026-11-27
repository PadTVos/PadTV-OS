"""Pinned build/test compilers and API stubs. Never shipped as runtime components."""
from pathlib import Path
import hashlib, urllib.request, zipfile, tempfile
root=Path(__file__).resolve().parents[1]/'build/test-tools';root.mkdir(parents=True,exist_ok=True)
files=[('r8.jar','https://dl.google.com/dl/android/maven2/com/android/tools/r8/8.3.37/r8-8.3.37.jar','59753e70a74f918389cc87f1b7d66b5c0862932559167425708ded159e3de439'),('android.jar','https://repo.maven.apache.org/maven2/com/google/android/android/4.1.1.4/android-4.1.1.4.jar','84072541cbb711eff89f7277100ff854929a446dba7ceb1b195c340e0b4fd3cb')]
for name,url,digest in files:
    path=root/name
    if not path.exists():
        with urllib.request.urlopen(url,timeout=60) as response:path.write_bytes(response.read(64*1024*1024+1))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise SystemExit('Test dependency checksum mismatch: '+name)
    print(name,digest)
# Official Google SDK API 35; extract only test compilation stubs.
path=root/'android35.jar'
digest='4566663c3876e022b4fa4ced8c8697c4ab1688267f090114fd92d027b32e619b'
if not path.exists():
    with tempfile.TemporaryFile() as archive:
        size=0;sha1=hashlib.sha1()
        with urllib.request.urlopen('https://dl.google.com/android/repository/platform-35_r02.zip',timeout=90) as response:
            while True:
                block=response.read(1024*1024)
                if not block:break
                size+=len(block)
                if size>150*1024*1024:raise SystemExit('SDK archive exceeds bound')
                sha1.update(block);archive.write(block)
        if sha1.hexdigest()!='0bb560a90a7a2cbd0dd8348224d518b638fe7949':raise SystemExit('Official SDK archive checksum mismatch')
        archive.seek(0)
        with zipfile.ZipFile(archive) as z:path.write_bytes(z.read('android-35/android.jar'))
if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise SystemExit('API 35 checksum mismatch')
print('android35.jar',digest)
