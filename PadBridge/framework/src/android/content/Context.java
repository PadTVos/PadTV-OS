package android.content;
import java.io.*;
import android.content.res.AssetManager;
public abstract class Context {
    private android.content.res.Resources resources;
    private android.content.res.Resources.Theme theme;
    public android.content.res.Resources.Theme getTheme(){if(theme==null)theme=getResources().newTheme();return theme;}
    public void setTheme(int id){getTheme().applyStyle(id,true);}
    public android.content.res.TypedArray obtainStyledAttributes(int[] attrs){return getTheme().obtainStyledAttributes(attrs);}
    public android.content.res.TypedArray obtainStyledAttributes(int style,int[] attrs){return getTheme().obtainStyledAttributes(style,attrs);}
    public android.content.res.TypedArray obtainStyledAttributes(android.util.AttributeSet set,int[] attrs){return getTheme().obtainStyledAttributes(set,attrs,0,0);}
    public android.content.res.TypedArray obtainStyledAttributes(android.util.AttributeSet set,int[] attrs,int defAttr,int defRes){return getTheme().obtainStyledAttributes(set,attrs,defAttr,defRes);}
    public static final int MODE_PRIVATE=0;
    public String getPackageName() { return org.padtv.bridge.Host.packageName; }
    public File getFilesDir() { File f=new File("/data/files"); if (!f.isDirectory()&&!f.mkdirs()) throw new IllegalStateException("Cannot create app files directory"); return f; }
    public File getCacheDir() { File f=new File("/data/cache"); if (!f.isDirectory()&&!f.mkdirs()) throw new IllegalStateException("Cannot create app cache directory"); return f; }
    private File file(String name) { if(name.contains("/")||name.equals(".")||name.equals(".."))throw new IllegalArgumentException("Invalid private filename"); return new File(getFilesDir(),name); }
    public FileOutputStream openFileOutput(String name,int mode) throws FileNotFoundException {
        if(mode!=MODE_PRIVATE) throw new UnsupportedOperationException("Only MODE_PRIVATE is supported");
        return new FileOutputStream(file(name));
    }
    public FileInputStream openFileInput(String name) throws FileNotFoundException { return new FileInputStream(file(name)); }
    public AssetManager getAssets() { return new AssetManager(); }
    public Context getApplicationContext() { return org.padtv.bridge.Host.application==null?this:org.padtv.bridge.Host.application; }
    public void registerComponentCallbacks(ComponentCallbacks c){org.padtv.bridge.Host.application.registerComponentCallbacks(c);}public void unregisterComponentCallbacks(ComponentCallbacks c){org.padtv.bridge.Host.application.unregisterComponentCallbacks(c);}
    public android.content.res.Resources getResources(){if(resources==null)resources=new android.content.res.Resources();return resources;}
    public String getString(int id){return getResources().getString(id);}public String getString(int id,Object... args){return getResources().getString(id,args);}public CharSequence getText(int id){return getResources().getText(id);}
    public SharedPreferences getSharedPreferences(String name,int mode){if(mode!=MODE_PRIVATE)throw new UnsupportedOperationException("Only private preferences supported");return org.padtv.bridge.Preferences.open(name);}
    public static final String LAYOUT_INFLATER_SERVICE="layout_inflater";
    public static final String ACTIVITY_SERVICE="activity";
    public android.content.pm.PackageManager getPackageManager(){return new android.content.pm.PackageManager();}
    public android.content.pm.ApplicationInfo getApplicationInfo(){try{return getPackageManager().getApplicationInfo(getPackageName(),0);}catch(android.content.pm.PackageManager.NameNotFoundException e){throw new IllegalStateException(e);}}
    public ClassLoader getClassLoader(){return getClass().getClassLoader();}
    public android.os.Looper getMainLooper(){return android.os.Looper.getMainLooper();}
    public void startActivity(Intent i){org.padtv.bridge.Host.launch(this,i);}
    public ComponentName startService(Intent i){return org.padtv.bridge.Components.start(this,i);}
    public boolean stopService(Intent i){return org.padtv.bridge.Components.stop(org.padtv.bridge.Components.target(this,i));}
    public Intent registerReceiver(BroadcastReceiver r,IntentFilter f){return org.padtv.bridge.Components.register(this,r,f);}
    public void unregisterReceiver(BroadcastReceiver r){org.padtv.bridge.Components.unregister(r);}
    public void sendBroadcast(Intent i){org.padtv.bridge.Components.broadcast(this,i);}
    public ContentResolver getContentResolver(){return new ContentResolver(this);}
    public File getDatabasePath(String name){if(name.contains("/")||name.contains("\\")||name.equals(".")||name.equals(".."))throw new IllegalArgumentException("Invalid database name");return new File("/data/databases",name);}
    public android.database.sqlite.SQLiteDatabase openOrCreateDatabase(String name,int mode,android.database.sqlite.SQLiteDatabase.CursorFactory factory){if(mode!=MODE_PRIVATE)throw new UnsupportedOperationException("Only private databases supported");return android.database.sqlite.SQLiteDatabase.openOrCreateDatabase(getDatabasePath(name),factory);}
    public Object getSystemService(String name) { if(name.equals(LAYOUT_INFLATER_SERVICE))return android.view.LayoutInflater.from(this);if(name.equals(ACTIVITY_SERVICE))return new android.app.ActivityManager();throw new UnsupportedOperationException("PadBridge system service unavailable: "+name); }
}
