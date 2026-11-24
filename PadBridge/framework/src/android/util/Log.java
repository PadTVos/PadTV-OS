package android.util;
public final class Log {
    private static int write(String level,String tag,String text){String s=level+"/"+tag+": "+text;System.err.println(s);return s.length();}
    public static int d(String tag,String text){return write("D",tag,text);}
    public static int i(String tag,String text){return write("I",tag,text);}
    public static int e(String tag,String text){return write("E",tag,text);}
    public static int w(String tag,String text){return write("W",tag,text);}
}
