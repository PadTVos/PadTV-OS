package android.view;
import android.graphics.*;
public interface SurfaceHolder {
 interface Callback {void surfaceCreated(SurfaceHolder h);void surfaceChanged(SurfaceHolder h,int format,int width,int height);void surfaceDestroyed(SurfaceHolder h);}
 interface Callback2 extends Callback {void surfaceRedrawNeeded(SurfaceHolder h);}
 void addCallback(Callback c);void removeCallback(Callback c);Surface getSurface();Rect getSurfaceFrame();Canvas lockCanvas();Canvas lockCanvas(Rect dirty);void unlockCanvasAndPost(Canvas c);void setFixedSize(int w,int h);void setSizeFromLayout();void setFormat(int f);void setKeepScreenOn(boolean keep);boolean isCreating();void setType(int type);
}
