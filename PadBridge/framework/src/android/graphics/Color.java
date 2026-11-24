package android.graphics;
public class Color {
 public static final int TRANSPARENT=0,BLACK=0xff000000,WHITE=0xffffffff,RED=0xffff0000,GREEN=0xff00ff00,BLUE=0xff0000ff,CYAN=0xff00ffff,MAGENTA=0xffff00ff,YELLOW=0xffffff00,GRAY=0xff888888;
 public static int rgb(int r,int g,int b){return argb(255,r,g,b);}public static int argb(int a,int r,int g,int b){return (a&255)<<24|(r&255)<<16|(g&255)<<8|(b&255);}
 public static int alpha(int c){return c>>>24;}public static int red(int c){return c>>16&255;}public static int green(int c){return c>>8&255;}public static int blue(int c){return c&255;}
 public static int parseColor(String s){if(s.startsWith("#")){long v=Long.parseLong(s.substring(1),16);if(s.length()==7)v|=0xff000000L;else if(s.length()!=9)throw new IllegalArgumentException(s);return (int)v;}throw new IllegalArgumentException("Unsupported color: "+s);}
}
