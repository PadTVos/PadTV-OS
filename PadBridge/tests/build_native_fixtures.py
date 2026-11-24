"""Compile an Android-target freestanding JNI library and original Java DEX."""
from pathlib import Path
from build_runtime_fixtures import OUT, ROOT, ANDROID, d8, package, run
import shutil

def build():
    work=OUT/'native06';work.mkdir(parents=True,exist_ok=True)
    classes=work/'classes';classes.mkdir(exist_ok=True)
    run('javac','--release','8','-cp',str(ANDROID),'-d',str(classes),str(ROOT/'tests/native06/NativeActivity.java'))
    d8(list(classes.rglob('*.class')),work)
    jdk=Path(shutil.which('javac')).resolve().parent.parent
    library=work/'libnativeprobe.so'
    run('clang','--target=x86_64-linux-android24','-fuse-ld=lld','-shared','-nostdlib','-fPIC','-fno-stack-protector',
        '-I'+str(jdk/'include'),'-I'+str(jdk/'include/linux'),'-I/usr/include/x86_64-linux-gnu',
        '-Wl,-z,defs',str(ROOT/'tests/native06/nativeprobe.c'),'-o',str(library))
    package(work,'native-jni','org.padtv.nativeprobe','org.padtv.nativeprobe.NativeActivity',
        [('classes.dex',work/'classes.dex')],extra={'lib/x86_64/libnativeprobe.so':library.read_bytes()})
    return OUT
if __name__=='__main__':print(build())
