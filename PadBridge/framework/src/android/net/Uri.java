package android.net;
public final class Uri {
    private final java.net.URI value;private Uri(String v){value=java.net.URI.create(v);}public static Uri parse(String v){return new Uri(v);}public static Uri fromFile(java.io.File f){return new Uri(f.toURI().toString());}
    public String getScheme(){return value.getScheme();}public String getAuthority(){return value.getAuthority();}public String getPath(){return value.getPath();}public String getLastPathSegment(){String p=getPath();return p==null?null:p.substring(p.lastIndexOf('/')+1);}public String toString(){return value.toString();}
}
