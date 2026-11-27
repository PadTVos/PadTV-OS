"""Supplemental real Java/Kotlin -> D8 APKs. Dependencies pinned by fetch-test-tools.py."""
import os,subprocess,zipfile,shutil
from pathlib import Path
from build_fixtures import ROOT,OUT,run
TOOLS=Path(os.environ.get('PADBRIDGE_TEST_TOOLS',ROOT/'build/test-tools'))
ANDROID=TOOLS/'android.jar'
def d8(inputs,out,api=26):
    run('java','-cp',str(TOOLS/'r8.jar'),'com.android.tools.r8.D8','--min-api',str(api),'--lib',str(ANDROID),'--output',str(out),*map(str,inputs))
def package(work,name,pkg,activity,code,split=None,extra=None,permissions=(),application_class=None):
    resources=work/'res';resources.mkdir(exist_ok=True)
    manifest=work/'AndroidManifest.xml'
    attr=f' split="{split}"' if split else ''
    application=f'<application><activity android:name="{activity}" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LEANBACK_LAUNCHER"/></intent-filter></activity></application>' if not split else '<application android:hasCode="true"/>'
    if pkg=='org.padtv.runtimeprobe' and not split:application=application.replace('</application>','<service android:name="org.padtv.runtimeprobe.ProbeService"/><provider android:name="org.padtv.runtimeprobe.ProbeProvider" android:authorities="org.padtv.probe" android:exported="false"/></application>')
    permission_xml=''.join(f'<uses-permission android:name="{p}"/>' for p in permissions)
    if application_class:application=application.replace('<application>',f'<application android:name="{application_class}">')
    manifest.write_text(f'<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{pkg}" android:versionCode="1" android:versionName="1.0"{attr}><uses-sdk android:minSdkVersion="21"/>{permission_xml}{application}</manifest>')
    unsigned=work/'unsigned.apk';run('aapt','package','-f','-M',str(manifest),'-I','/usr/share/android-framework-res/framework-res.apk','-S',str(resources),'-F',str(unsigned))
    with zipfile.ZipFile(unsigned,'a') as z:
        for n,p in code:z.write(p,n)
        for n,b in (extra or {}).items():z.writestr(n,b)
    run('apksigner','sign','--ks',str(OUT/'test.keystore'),'--ks-pass','pass:testonly','--out',str(OUT/(name+'.apk')),str(unsigned))
def build():
    work=OUT/'runtime05';work.mkdir(parents=True,exist_ok=True);classes=work/'classes';classes.mkdir(exist_ok=True)
    run('javac','--release','8','-cp',str(ANDROID),'-d',str(classes),*map(str,(ROOT/'tests/java').glob('*.java')))
    secondary=classes/'org/padtv/runtimeprobe/Secondary.class'
    dex=work/'main';dex.mkdir(exist_ok=True);aux=work/'secondary';aux.mkdir(exist_ok=True)
    d8([p for p in classes.rglob('*.class') if p!=secondary],dex);d8([secondary],aux)
    res=work/'res';(res/'layout').mkdir(parents=True,exist_ok=True);(res/'values').mkdir(exist_ok=True)
    (res/'values/strings.xml').write_text('<resources><string name="title">Compiled Android XML</string></resources>')
    (res/'layout/main.xml').write_text('''<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android" android:orientation="vertical" android:layout_width="match_parent" android:layout_height="match_parent"><TextView android:id="@+id/result" android:text="@string/title" android:layout_width="match_parent" android:layout_height="wrap_content"/><LinearLayout android:orientation="horizontal" android:layout_width="match_parent" android:layout_height="wrap_content"><Button android:text="Select" android:onClick="select" android:layout_width="240dp" android:layout_height="80dp"/><Button android:text="Second" android:onClick="select" android:layout_width="240dp" android:layout_height="80dp"/></LinearLayout></LinearLayout>''')
    package(work,'java-multidex','org.padtv.runtimeprobe','org.padtv.runtimeprobe.RuntimeActivity',[('classes.dex',dex/'classes.dex'),('classes2.dex',aux/'classes.dex')])
    package(work,'split-base','org.padtv.runtimeprobe','org.padtv.runtimeprobe.RuntimeActivity',[('classes.dex',dex/'classes.dex')])
    split=OUT/'split05';split.mkdir(exist_ok=True)
    package(split,'split-feature','org.padtv.runtimeprobe','',[('classes.dex',aux/'classes.dex')],split='feature.code',extra={'assets/from-split.txt':b'SPLIT_ASSET_OK'})
    with zipfile.ZipFile(OUT/'runtime.apks','w') as z:
        for p in ['split-base.apk','split-feature.apk']:z.write(OUT/p,p)
    kotlin=OUT/'kotlin05';kotlin.mkdir(exist_ok=True)
    run('kotlinc','-jvm-target','1.8','-cp',str(ANDROID),'-include-runtime','-d',str(kotlin/'classes.jar'),str(ROOT/'tests/kotlin/KotlinActivity.kt'))
    d8([kotlin/'classes.jar'],kotlin,28)
    package(kotlin,'kotlin','org.padtv.kotlinprobe','org.padtv.kotlinprobe.KotlinActivity',[('classes.dex',kotlin/'classes.dex')])
    return OUT
if __name__=='__main__':print(build())
