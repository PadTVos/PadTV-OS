package org.padtv.bridge;
/** Internal, serialized JNI transport. It never invents successful media output. */
public final class MediaNative {
 static { System.loadLibrary("padbridge_media"); }
 private MediaNative(){}
 public static synchronized native long open(String path) throws java.io.IOException;
 public static synchronized native int trackCount(long h);
 public static synchronized native String[] trackFormat(long h,int track);
 public static synchronized native byte[] extra(long h,int track);
 public static synchronized native boolean next(long h) throws java.io.IOException;
 public static synchronized native byte[] packet(long h);
 public static synchronized native long[] packetInfo(long h);
 public static synchronized native void seek(long h,long us,int mode);
 public static synchronized native long decoder(int codec,int width,int height,int rate,int channels,byte[] extra) throws java.io.IOException;
 public static synchronized native int send(long h,byte[] packet,long pts);
 public static synchronized native byte[] receive(long h);
 public static synchronized native long[] frameInfo(long h);
 public static synchronized native void flushDecoder(long h);
 public static synchronized native long audioOpen(int rate,int channels);
 public static synchronized native void audioWrite(long h,byte[] pcm);
 public static synchronized native long audioLatency(long h);
 public static synchronized native void audioControl(long h,boolean drain);
 public static synchronized native void audioPause(long h,boolean paused);
 public static synchronized native void audioClose(long h);
 public static synchronized native void close(long h,int kind);
 public static synchronized native int codecId(String mime);
}
