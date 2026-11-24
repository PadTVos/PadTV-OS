"""Build original signed Android APKs from reviewable smali sources, no SDK download."""
from pathlib import Path
import struct, subprocess, zlib, zipfile

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fixtures'

def run(*args,cwd=None):
    subprocess.run(args,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def png():
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    pixels=b''.join(b'\0'+b''.join(bytes((x*4,y*4,180)) for x in range(64)) for y in range(64))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',64,64,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b'')

def activity(body):
    return '''.class public Lorg/padtv/fixture/Main;
.super Landroid/app/Activity;
.method public constructor <init>()V
 .locals 0
 invoke-direct {p0}, Landroid/app/Activity;-><init>()V
 return-void
.end method
.method protected onCreate(Landroid/os/Bundle;)V
 .locals 8
'''+body+'''\n return-void
.end method
'''

NETWORK=activity('''
 const-string v0, "url.txt"
 invoke-virtual {p0,v0}, Landroid/content/Context;->openFileInput(Ljava/lang/String;)Ljava/io/FileInputStream;
 move-result-object v0
 new-instance v1, Ljava/util/Scanner;
 invoke-direct {v1,v0}, Ljava/util/Scanner;-><init>(Ljava/io/InputStream;)V
 invoke-virtual {v1}, Ljava/util/Scanner;->nextLine()Ljava/lang/String;
 move-result-object v2
 invoke-virtual {v1}, Ljava/util/Scanner;->close()V
 new-instance v0, Ljava/net/URL;
 invoke-direct {v0,v2}, Ljava/net/URL;-><init>(Ljava/lang/String;)V
 invoke-virtual {v0}, Ljava/net/URL;->openConnection()Ljava/net/URLConnection;
 move-result-object v0
 const/16 v1, 0x7d0
 invoke-virtual {v0,v1}, Ljava/net/URLConnection;->setConnectTimeout(I)V
 invoke-virtual {v0,v1}, Ljava/net/URLConnection;->setReadTimeout(I)V
 invoke-virtual {v0}, Ljava/net/URLConnection;->getInputStream()Ljava/io/InputStream;
 move-result-object v0
 new-instance v1, Ljava/util/Scanner;
 invoke-direct {v1,v0}, Ljava/util/Scanner;-><init>(Ljava/io/InputStream;)V
 invoke-virtual {v1}, Ljava/util/Scanner;->nextLine()Ljava/lang/String;
 move-result-object v0
 invoke-virtual {v1}, Ljava/util/Scanner;->close()V
 const-string v1, "NETWORK"
 invoke-static {v1,v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
''')
ISOLATION=activity('''
 new-instance v0, Ljava/io/File;
 const-string v1, "/tmp/padbridge-host-secret"
 invoke-direct {v0,v1}, Ljava/io/File;-><init>(Ljava/lang/String;)V
 invoke-virtual {v0}, Ljava/io/File;->exists()Z
 move-result v0
 if-nez v0,:bad
 new-instance v0, Ljava/io/File;
 const-string v1, "/home/padtv"
 invoke-direct {v0,v1}, Ljava/io/File;-><init>(Ljava/lang/String;)V
 invoke-virtual {v0}, Ljava/io/File;->exists()Z
 move-result v0
 if-nez v0,:bad
 const-string v0, "ISOLATION"
 const-string v1, "HOST_PATHS_HIDDEN_OK"
 invoke-static {v0,v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
 goto :done
 :bad
 new-instance v0, Ljava/lang/IllegalStateException;
 invoke-direct {v0}, Ljava/lang/IllegalStateException;-><init>()V
 throw v0
 :done
''')
CRASH=activity('''
 invoke-virtual {p0}, Landroid/content/Context;->getFilesDir()Ljava/io/File;
 move-result-object v0
 new-instance v1, Ljava/io/File;
 const-string v2, "attempted"
 invoke-direct {v1,v0,v2}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V
 invoke-virtual {v1}, Ljava/io/File;->exists()Z
 move-result v0
 if-nez v0,:recovered
 invoke-virtual {v1}, Ljava/io/File;->createNewFile()Z
 const/16 v0, 23
 invoke-static {v0}, Ljava/lang/System;->exit(I)V
 :recovered
 const-string v0, "CRASH"
 const-string v1, "CRASH_RECOVERY_OK"
 invoke-static {v0,v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
''')
MEDIA=activity('''
 const-string v0, "video/avc"
 invoke-static {v0}, Landroid/media/MediaCodec;->createDecoderByType(Ljava/lang/String;)Landroid/media/MediaCodec;
''')
AUDIO=activity('''
 const/4 v0, 1
 invoke-static {v0}, Landroid/media/AudioTrack;->getNativeOutputSampleRate(I)I
''')

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    for key in ('test','other'):
        path=OUT/(key+'.keystore')
        if not path.exists():run('keytool','-genkeypair','-keystore',str(path),'-storepass','testonly','-keypass','testonly','-alias','fixture','-keyalg','RSA','-keysize','2048','-validity','3650','-dname','CN=PadBridge Test Only')
    variants=[('basic',1,'test',None),('update',2,'test',None),('wrong-signer',2,'other',None),
        ('network',1,'test',NETWORK),('isolation',1,'test',ISOLATION),('crash',1,'test',CRASH),
        ('media',1,'test',MEDIA),('audio',1,'test',AUDIO),('native',1,'test',None),('tvonly',1,'test',None)]
    for name,version,key,body in variants:
        work=OUT/name;work.mkdir(exist_ok=True)
        src=work/'smali';src.mkdir(exist_ok=True)
        for p in src.glob('*.smali'):p.unlink()
        if body is None:
            for p in (ROOT/'tests/fixtures').glob('*.smali'):(src/p.name).write_bytes(p.read_bytes())
        else:(src/'Main.smali').write_text(body,encoding='utf-8')
        package='org.padtv.fixture.'+('basic' if name in ('basic','update','wrong-signer') else name)
        (work/'assets').mkdir(exist_ok=True);(work/'assets/test.png').write_bytes(png())
        (work/'res/drawable').mkdir(parents=True,exist_ok=True);(work/'res/drawable/icon.png').write_bytes(png())
        permissions='<uses-permission android:name="android.permission.INTERNET"/>' if name=='network' else ''
        (work/'AndroidManifest.xml').write_text(f'''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{package}" android:versionCode="{version}" android:versionName="{version}.0">
<uses-sdk android:minSdkVersion="21" android:targetSdkVersion="28"/>{permissions}
<uses-feature android:name="android.software.leanback" android:required="false"/>
<application android:label="PadBridge {name}" android:icon="@drawable/icon"><activity android:name="org.padtv.fixture.Main" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/><category android:name="android.intent.category.LEANBACK_LAUNCHER"/></intent-filter></activity></application></manifest>''')
        if name=='tvonly':
            manifest=work/'AndroidManifest.xml'
            manifest.write_text(manifest.read_text().replace('<category android:name="android.intent.category.LAUNCHER"/>',''))
        run('java','-jar','/usr/share/java/smali.jar','assemble',str(src),'--api','23','-o',str(work/'classes.dex'))
        run('aapt','package','-f','-M',str(work/'AndroidManifest.xml'),'-I','/usr/share/android-framework-res/framework-res.apk','-S',str(work/'res'),'-A',str(work/'assets'),'-F',str(work/'unsigned.apk'))
        with zipfile.ZipFile(work/'unsigned.apk','a') as apk:
            apk.write(work/'classes.dex','classes.dex')
            if name=='native':
                (work/'probe.c').write_text('#include <stdio.h>\nint padbridge_probe(void) { return puts("native-test"); }\n')
                run('cc','-shared','-fPIC','-o',str(work/'libprobe.so'),str(work/'probe.c'))
                apk.write(work/'libprobe.so','lib/x86_64/libprobe.so')
        run('apksigner','sign','--ks',str(OUT/(key+'.keystore')),'--ks-pass','pass:testonly','--out',str(OUT/(name+'.apk')),str(work/'unsigned.apk'))
    return OUT

if __name__=='__main__':print(build())
