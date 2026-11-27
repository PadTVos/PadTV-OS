package android.content;
public class ContextWrapper extends Context {
 private Context base;
 public ContextWrapper(Context c){base=c;}protected void attachBaseContext(Context c){if(base!=null)throw new IllegalStateException("Base context already attached");if(c==null)throw new NullPointerException();base=c;}
 public Context getBaseContext(){if(base==null)throw new IllegalStateException("Context not attached");return base;}
 public android.content.res.Resources.Theme getTheme(){return getBaseContext().getTheme();}public void setTheme(int id){getBaseContext().setTheme(id);}
 public Context getApplicationContext(){return getBaseContext().getApplicationContext();}public String getPackageName(){return getBaseContext().getPackageName();}public java.io.File getFilesDir(){return getBaseContext().getFilesDir();}public java.io.File getCacheDir(){return getBaseContext().getCacheDir();}public android.content.res.Resources getResources(){return getBaseContext().getResources();}public android.content.res.AssetManager getAssets(){return getBaseContext().getAssets();}public SharedPreferences getSharedPreferences(String name,int mode){return getBaseContext().getSharedPreferences(name,mode);}public Object getSystemService(String name){return getBaseContext().getSystemService(name);}public android.content.pm.PackageManager getPackageManager(){return getBaseContext().getPackageManager();}
}
