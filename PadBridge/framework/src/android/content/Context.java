package android.content;
import java.io.*;
import android.content.res.AssetManager;
public abstract class Context {
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
    public Context getApplicationContext() { return this; }
    public Object getSystemService(String name) { throw new UnsupportedOperationException("PadBridge system service unavailable: "+name); }
}
