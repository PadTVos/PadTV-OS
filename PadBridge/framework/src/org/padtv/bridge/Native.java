package org.padtv.bridge;

public final class Native {
    static { System.loadLibrary("padbridge_native"); }
    public static native int create(int kind);
    public static native void text(int id, String text);
    public static native void image(int id, byte[] bytes);
    public static native void child(int parent, int child);
    public static native void layout(int id,int orientation);
    public static native void size(int id,int width,int height);
    public static native void root(int id);
    public static native void focus(int id);
    public static native void visibility(int id,int value);
    public static native void windowFlags(int flags);
    public static native int[] displaySize();
    public static native void layoutScene(int width,int height);
    public static native void run();
    public static native String snapshot();
}
