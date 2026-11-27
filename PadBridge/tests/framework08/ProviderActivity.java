package org.padtv.frameworkprobe;
import android.app.*;import android.content.*;import android.content.pm.*;import android.os.*;import android.database.*;import android.net.Uri;
public class ProviderActivity extends Activity {
    static String order="";static int instances;
    public static class App extends Application {public void onCreate(){super.onCreate();if(!order.equals("HL")||instances!=2)throw new AssertionError("Providers must precede application.onCreate: "+order);order+="A";}}
    public static class High extends ContentProvider {
        public boolean onCreate(){if(getContext()==null||getContext().getApplicationContext()==null)throw new AssertionError("Provider context");order+="H";instances++;return true;}
        public String getType(Uri u){return "vnd.original/high";}
        public Cursor query(Uri u,String[] p,String s,String[] a,String sort){throw new UnsupportedOperationException("Test provider has no rows");}public Uri insert(Uri u,ContentValues v){throw new UnsupportedOperationException();}public int delete(Uri u,String s,String[] a){throw new UnsupportedOperationException();}public int update(Uri u,ContentValues v,String s,String[] a){throw new UnsupportedOperationException();}
    }
    public static class Low extends High {public boolean onCreate(){order+="L";instances++;return true;}}
    public static class Disabled extends High {public boolean onCreate(){throw new AssertionError("Disabled/remote provider was initialized");}}
    public static class Fails extends High {public boolean onCreate(){return false;}}
    protected void onCreate(Bundle state){super.onCreate(state);try{
        if(!order.equals("HLA"))throw new AssertionError("Activity lifecycle order");
        ProviderInfo info=getPackageManager().getProviderInfo(new ComponentName(this,High.class),PackageManager.GET_META_DATA);
        if(!info.metaData.getString("text").equals("false")||!info.metaData.getBoolean("enabled")||info.metaData.getInt("count")!=42)throw new AssertionError("Metadata types: "+info.metaData);
        if(getPackageManager().getProviderInfo(new ComponentName(this,High.class),0).metaData!=null)throw new AssertionError("GET_META_DATA flag");
        if(!getContentResolver().getType(Uri.parse("content://org.padtv.high/a")).equals("vnd.original/high")||!getContentResolver().getType(Uri.parse("content://org.padtv.alias/b")).equals("vnd.original/high")||instances!=2)throw new AssertionError("Authority aliases must share one provider");
        try{getContentResolver().getType(Uri.parse("content://outside.app/a"));throw new AssertionError("External provider exposed");}catch(UnsupportedOperationException expected){}
        System.out.println("ORIGINAL_PROVIDER_ORDER_METADATA_ALIAS_ISOLATION_OK");
    }catch(PackageManager.NameNotFoundException error){throw new IllegalStateException(error);}}
}
