"""Compile against the real Android SDK; execute original DEX in PadBridge."""
from build_runtime_fixtures import ROOT,OUT,TOOLS,run,package
def build():
    work=OUT/'framework08';work.mkdir(exist_ok=True);classes=work/'classes';classes.mkdir(exist_ok=True)
    android=TOOLS/'android35.jar'
    run('javac','--release','8','-cp',str(android),'-d',str(classes),*map(str,(ROOT/'tests/framework08').glob('*.java')))
    run('java','-cp',str(TOOLS/'r8.jar'),'com.android.tools.r8.D8','--min-api','26','--lib',str(android),'--output',str(work),*map(str,classes.rglob('*.class')))
    res=work/'res/values';res.mkdir(exist_ok=True)
    (res/'themes.xml').write_text('''<resources><attr name="tileGap" format="dimension"/><attr name="headlineColor" format="color"/><attr name="caption" format="string"/><attr name="missing" format="string"/><string name="title">Original resource text</string><style name="Base"><item name="tileGap">12dp</item><item name="headlineColor">#ff123456</item><item name="caption">@string/title</item></style><style name="Child" parent="Base"><item name="tileGap">24dp</item><item name="headlineColor">#ffabcdef</item></style></resources>''')
    (res/'literal.xml').write_text('<resources><string name="numeric">123</string><string name="boolean_text">false</string><string name="dimension_text">12dp</string><string name="marker_text">!bag|1|bad</string><style name="Literal"><item name="caption">false</item></style></resources>')
    package(work,'layout08','org.padtv.frameworkprobe','org.padtv.frameworkprobe.LayoutActivity',[('classes.dex',work/'classes.dex')])
    package(work,'theme08','org.padtv.themeprobe','org.padtv.frameworkprobe.ThemeActivity',[('classes.dex',work/'classes.dex')])
    package(work,'scroll08','org.padtv.scrollprobe','org.padtv.frameworkprobe.ScrollActivity',[('classes.dex',work/'classes.dex')])
    package(work,'menu08','org.padtv.menuprobe','org.padtv.frameworkprobe.MenuActivity',[('classes.dex',work/'classes.dex')])
    package(work,'keys08','org.padtv.keyprobe','org.padtv.frameworkprobe.KeyActivity',[('classes.dex',work/'classes.dex')])
    package(work,'bundle08','org.padtv.bundleprobe','org.padtv.frameworkprobe.BundleActivity',[('classes.dex',work/'classes.dex')])
    package(work,'parcel08','org.padtv.parcelprobe','org.padtv.frameworkprobe.ParcelActivity',[('classes.dex',work/'classes.dex')])
    package(work,'xml08','org.padtv.xmlprobe','org.padtv.frameworkprobe.XmlActivity',[('classes.dex',work/'classes.dex')])
    package(work,'size08','org.padtv.sizeprobe','org.padtv.frameworkprobe.SizeActivity',[('classes.dex',work/'classes.dex')])
    package(work,'rating08','org.padtv.ratingprobe','org.padtv.frameworkprobe.RatingActivity',[('classes.dex',work/'classes.dex')])
    package(work,'build08','org.padtv.buildprobe','org.padtv.frameworkprobe.BuildActivity',[('classes.dex',work/'classes.dex')])
    package(work,'trace08','org.padtv.traceprobe','org.padtv.frameworkprobe.TraceActivity',[('classes.dex',work/'classes.dex')])
    (res/'provider.xml').write_text('<resources><string name="metadata_text">false</string></resources>')
    providers='''<provider android:name="org.padtv.frameworkprobe.ProviderActivity$Low" android:authorities="org.padtv.low" android:initOrder="1" android:exported="false"/><provider android:name="org.padtv.frameworkprobe.ProviderActivity$High" android:authorities="org.padtv.high;org.padtv.alias" android:initOrder="100" android:exported="false"><meta-data android:name="text" android:value="@string/metadata_text"/><meta-data android:name="enabled" android:value="true"/><meta-data android:name="count" android:value="42"/></provider><provider android:name="org.padtv.frameworkprobe.ProviderActivity$Disabled" android:authorities="org.padtv.disabled" android:enabled="false" android:exported="false"/><provider android:name="org.padtv.frameworkprobe.ProviderActivity$Disabled" android:authorities="org.padtv.remote" android:process=":remote" android:exported="false"/>'''
    package(work,'providers08','org.padtv.providerprobe','org.padtv.frameworkprobe.ProviderActivity',[('classes.dex',work/'classes.dex')],application_class='org.padtv.frameworkprobe.ProviderActivity$App',components=providers)
    package(work,'provider-fails08','org.padtv.providerfails','org.padtv.frameworkprobe.BuildActivity',[('classes.dex',work/'classes.dex')],components='<provider android:name="org.padtv.frameworkprobe.ProviderActivity$Fails" android:authorities="org.padtv.failed" android:exported="false"/>')
    return OUT
if __name__=='__main__':print(build())
