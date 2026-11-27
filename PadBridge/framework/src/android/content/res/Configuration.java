package android.content.res;
/** Configuration snapshot for the current bridge display; no device certification. */
public class Configuration {
 public static final int ORIENTATION_UNDEFINED=0,ORIENTATION_PORTRAIT=1,ORIENTATION_LANDSCAPE=2,UI_MODE_TYPE_TELEVISION=4,UI_MODE_NIGHT_NO=16,UI_MODE_NIGHT_YES=32;
 public java.util.Locale locale=java.util.Locale.getDefault();public float fontScale=1;public int orientation,screenWidthDp,screenHeightDp,densityDpi=160,uiMode=UI_MODE_TYPE_TELEVISION|UI_MODE_NIGHT_NO;
 public Configuration(){int[] size=org.padtv.bridge.Native.displaySize();screenWidthDp=size[0];screenHeightDp=size[1];orientation=size[0]>=size[1]?2:1;}
 public Configuration(Configuration other){setTo(other);}public void setTo(Configuration c){locale=c.locale;fontScale=c.fontScale;orientation=c.orientation;screenWidthDp=c.screenWidthDp;screenHeightDp=c.screenHeightDp;densityDpi=c.densityDpi;uiMode=c.uiMode;}
}
