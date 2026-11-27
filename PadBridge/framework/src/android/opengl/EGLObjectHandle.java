package android.opengl;
public abstract class EGLObjectHandle {final long handle;EGLObjectHandle(long h){handle=h;}public long getNativeHandle(){return handle;}public int hashCode(){return (int)(handle^(handle>>>32));}public boolean equals(Object o){return o!=null&&o.getClass()==getClass()&&((EGLObjectHandle)o).handle==handle;}}
