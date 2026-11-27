"""SDK-compiled media API exercise APK and deterministic non-DRM test clip."""
from build_runtime_fixtures import OUT, ROOT, TOOLS, package, run
import shutil
from pathlib import Path

def build():
    work=OUT/'media07';work.mkdir(parents=True,exist_ok=True)
    classes=work/'classes';classes.mkdir(exist_ok=True)
    android=TOOLS/'android35.jar'
    run('javac','--release','8','-cp',str(android),'-d',str(classes),*map(str,(ROOT/'tests/media07').glob('*.java')))
    run('java','-cp',str(TOOLS/'r8.jar'),'com.android.tools.r8.D8','--min-api','26','--lib',str(android),'--output',str(work),*map(str,classes.rglob('*.class')))
    package(work,'media07','org.padtv.mediaprobe','org.padtv.mediaprobe.MediaActivity',[('classes.dex',work/'classes.dex')],permissions=['android.permission.INTERNET'])
    package(work,'mediapeer07','org.padtv.mediapeer','org.padtv.mediaprobe.MediaActivity',[('classes.dex',work/'classes.dex')],permissions=['android.permission.INTERNET'])
    package(work,'web07','org.padtv.webprobe','org.padtv.webprobe.WebActivity',[('classes.dex',work/'classes.dex')])
    package(work,'gl07','org.padtv.glprobe','org.padtv.glprobe.GLActivity',[('classes.dex',work/'classes.dex')])
    package(work,'lifecycle07','org.padtv.lifecycleprobe','org.padtv.lifecycleprobe.LifecycleActivity',[('classes.dex',work/'classes.dex')],application_class='org.padtv.lifecycleprobe.ProbeApplication')
    jdk=Path(shutil.which('javac')).resolve().parent.parent
    # Link-only declarations; these bytes are NEVER included in the APK/runtime.
    (work/'link-declarations.c').write_text('void *malloc(unsigned long n){return 0;} void free(void*p){} void *memcpy(void*a,const void*b,unsigned long n){return a;} int memcmp(const void*a,const void*b,unsigned long n){return 0;} int __system_property_get(const char*n,char*v){return 0;}')
    flags=['clang','--target=x86_64-linux-android24','-fuse-ld=lld','-shared','-nostdlib','-fPIC','-fno-stack-protector','-fno-builtin']
    run(*flags,'-Wl,-soname,libc.so',str(work/'link-declarations.c'),'-o',str(work/'libc.so'))
    run(*flags,'-I'+str(jdk/'include'),'-I'+str(jdk/'include/linux'),'-I/usr/include/x86_64-linux-gnu',str(ROOT/'tests/media07/abi.c'),'-L'+str(work),'-Wl,--no-as-needed','-l:libc.so','-Wl,-z,defs','-o',str(work/'libabiprobe.so'))
    package(work,'abi07','org.padtv.abiprobe','org.padtv.abiprobe.AbiActivity',[('classes.dex',work/'classes.dex')],extra={'lib/x86_64/libabiprobe.so':(work/'libabiprobe.so').read_bytes()})
    package(work,'reject07','org.padtv.rejectprobe','org.padtv.rejectprobe.RejectActivity',[('classes.dex',work/'classes.dex')],extra={'lib/x86_64/libhostbad.so':(OUT/'native/libprobe.so').read_bytes()})
    zero=OUT/'zero07';zero.mkdir(exist_ok=True)
    run('java','-jar','/usr/share/java/smali.jar','assemble',str(ROOT/'tests/media07/Zero.smali'),'--api','23','-o',str(zero/'classes.dex'))
    package(zero,'zero07','org.padtv.zero','org.padtv.zero.Zero',[('classes.dex',zero/'classes.dex')])
    ctors=OUT/'ctors07';ctors.mkdir(exist_ok=True)
    run('java','-jar','/usr/share/java/smali.jar','assemble',str(ROOT/'tests/media07/constructors'),'--api','23','-o',str(ctors/'classes.dex'))
    package(ctors,'ctors07','org.padtv.ctors','org.padtv.ctors.Main',[('classes.dex',ctors/'classes.dex')])
    run('ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=160x90:rate=25','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','1.2','-c:v','libx264','-pix_fmt','yuv420p','-g','25','-bf','2','-c:a','aac','-movflags','+faststart',str(OUT/'media07.mp4'))
    return OUT

if __name__=='__main__':print(build())
