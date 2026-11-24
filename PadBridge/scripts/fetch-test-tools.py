"""Pinned test-only compilers/API stubs. Never shipped as runtime components."""
from pathlib import Path
import hashlib, urllib.request
root=Path(__file__).resolve().parents[1]/'build/test-tools';root.mkdir(parents=True,exist_ok=True)
files=[('r8.jar','https://dl.google.com/dl/android/maven2/com/android/tools/r8/8.3.37/r8-8.3.37.jar','59753e70a74f918389cc87f1b7d66b5c0862932559167425708ded159e3de439'),('android.jar','https://repo.maven.apache.org/maven2/com/google/android/android/4.1.1.4/android-4.1.1.4.jar','84072541cbb711eff89f7277100ff854929a446dba7ceb1b195c340e0b4fd3cb')]
for name,url,digest in files:
    path=root/name
    if not path.exists():
        with urllib.request.urlopen(url,timeout=60) as response:path.write_bytes(response.read(64*1024*1024+1))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise SystemExit('Test dependency checksum mismatch: '+name)
    print(name,digest)
