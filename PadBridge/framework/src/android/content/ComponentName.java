package android.content;
public final class ComponentName {
    private final String pkg,cls;public ComponentName(String p,String c){pkg=p;cls=c.startsWith(".")?p+c:c;}public ComponentName(Context c,Class<?> k){this(c.getPackageName(),k.getName());}
    public String getPackageName(){return pkg;}public String getClassName(){return cls;}public String flattenToString(){return pkg+"/"+cls;}
    public boolean equals(Object o){return o instanceof ComponentName&&flattenToString().equals(((ComponentName)o).flattenToString());}public int hashCode(){return flattenToString().hashCode();}
}
