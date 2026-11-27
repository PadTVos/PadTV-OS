package android.view;
import android.graphics.*;
import android.content.Context;
import java.util.*;
public class SurfaceView extends View {
 private final Holder holder=new Holder();
 public SurfaceView(Context c){super(c);canvasDrawing=false;}public SurfaceView(Context c,android.util.AttributeSet a){this(c);}public SurfaceView(Context c,android.util.AttributeSet a,int style){this(c);}
 public SurfaceHolder getHolder(){return holder;}
 protected void onSizeChanged(int w,int h,int ow,int oh){super.onSizeChanged(w,h,ow,oh);holder.update(w,h);}
 protected void onDetachedFromWindow(){holder.destroy();super.onDetachedFromWindow();}
 protected void onAttachedToWindow(){super.onAttachedToWindow();if(getWidth()>0&&getHeight()>0)holder.update(getWidth(),getHeight());}
 private final class Holder implements SurfaceHolder {
  private final List<Callback> callbacks=new ArrayList<Callback>();private Surface surface;private int fixedW,fixedH;private boolean creating;
  public void addCallback(Callback c){if(!callbacks.contains(c))callbacks.add(c);}public void removeCallback(Callback c){callbacks.remove(c);}
  void update(int w,int h){if(w<=0||h<=0)return;if(fixedW>0){w=fixedW;h=fixedH;}boolean first=surface==null||!surface.isValid();if(first)surface=new Surface(bridgeId,w,h);else surface.resize(w,h);creating=first;try{for(Callback c:new ArrayList<Callback>(callbacks)){if(first)c.surfaceCreated(this);c.surfaceChanged(this,1,w,h);}}finally{creating=false;}}
  void destroy(){if(surface!=null&&surface.isValid()){for(Callback c:new ArrayList<Callback>(callbacks))c.surfaceDestroyed(this);surface.release();}}
  public Surface getSurface(){return surface;}public Rect getSurfaceFrame(){return new Rect(0,0,fixedW>0?fixedW:getWidth(),fixedH>0?fixedH:getHeight());}
  public Canvas lockCanvas(){return lockCanvas(null);}public Canvas lockCanvas(Rect r){if(surface==null)throw new IllegalStateException("Surface not created");return surface.lockCanvas(r);}public void unlockCanvasAndPost(Canvas c){surface.unlockCanvasAndPost(c);}
  public void setFixedSize(int w,int h){if(w<1||h<1||(long)w*h>8388608)throw new IllegalArgumentException();fixedW=w;fixedH=h;if(surface!=null)update(w,h);}public void setSizeFromLayout(){fixedW=fixedH=0;if(surface!=null)update(getWidth(),getHeight());}
  public void setFormat(int f){if(f!=1&&f!=-1&&f!=-3)throw new UnsupportedOperationException("Only RGBA surfaces");}public void setKeepScreenOn(boolean keep){org.padtv.bridge.Native.windowFlags(keep?128:0);}public boolean isCreating(){return creating;}public void setType(int t){if(t!=0&&t!=3)throw new UnsupportedOperationException("Surface type");}
 }
}
