package android.opengl;
public final class EGLSurface extends EGLObjectHandle {final android.view.Surface target;final int width,height;EGLSurface(long h,android.view.Surface t,int w,int size){super(h);target=t;width=w;height=size;}}
