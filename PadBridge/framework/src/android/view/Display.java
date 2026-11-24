package android.view;
public class Display {
 public void getRealMetrics(android.util.DisplayMetrics m){int[] size=org.padtv.bridge.Native.displaySize();m.widthPixels=size[0];m.heightPixels=size[1];}
 public void getMetrics(android.util.DisplayMetrics m){getRealMetrics(m);}public int getWidth(){return org.padtv.bridge.Native.displaySize()[0];}public int getHeight(){return org.padtv.bridge.Native.displaySize()[1];}
}
