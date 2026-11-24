package android.content;
import android.os.Bundle;
public class Intent {
    public static final String ACTION_MAIN="android.intent.action.MAIN",ACTION_VIEW="android.intent.action.VIEW",CATEGORY_LAUNCHER="android.intent.category.LAUNCHER",CATEGORY_LEANBACK_LAUNCHER="android.intent.category.LEANBACK_LAUNCHER";
    public static final int FLAG_ACTIVITY_NEW_TASK=0x10000000;
    private String action,pkg;private ComponentName component;private int flags;private android.net.Uri data;private Bundle extras=new Bundle();private final java.util.Set<String> categories=new java.util.HashSet<String>();
    public Intent(){}public Intent(String a){action=a;}public Intent(Context c,Class<?> k){component=new ComponentName(c,k);}public Intent(String a,android.net.Uri u){action=a;data=u;}
    public String getAction(){return action;}public Intent setAction(String a){action=a;return this;}public Intent setComponent(ComponentName c){component=c;return this;}public ComponentName getComponent(){return component;}
    public Intent setClass(Context c,Class<?> k){return setComponent(new ComponentName(c,k));}public Intent setClassName(String p,String c){return setComponent(new ComponentName(p,c));}
    public Intent setPackage(String p){pkg=p;return this;}public String getPackage(){return pkg;}public Intent addCategory(String c){categories.add(c);return this;}public java.util.Set<String> getCategories(){return java.util.Collections.unmodifiableSet(categories);}
    public Intent setFlags(int f){flags=f;return this;}public Intent addFlags(int f){flags|=f;return this;}public int getFlags(){return flags;}
    public Intent setData(android.net.Uri u){data=u;return this;}public android.net.Uri getData(){return data;}
    public Intent putExtra(String k,String v){extras.putString(k,v);return this;}public Intent putExtra(String k,int v){extras.putInt(k,v);return this;}public Intent putExtra(String k,boolean v){extras.putBoolean(k,v);return this;}
    public String getStringExtra(String k){return extras.getString(k);}public int getIntExtra(String k,int d){return extras.containsKey(k)?extras.getInt(k):d;}public boolean getBooleanExtra(String k,boolean d){return extras.containsKey(k)?extras.getBoolean(k):d;}public Bundle getExtras(){return extras;}
}
