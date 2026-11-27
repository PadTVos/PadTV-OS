package android.view;
import android.graphics.*;
import java.nio.ByteBuffer;
/** A compositor-presented CPU surface. EGL window surfaces are a separate path. */
public class Surface {
 private final int view;private volatile boolean valid=true;private int width,height;private Canvas locked;private Bitmap bitmap;
 Surface(int id,int w,int h){view=id;width=w;height=h;}
 public boolean isValid(){return valid;}public synchronized void release(){valid=false;locked=null;bitmap=null;}
 public synchronized int bridgeWidth(){check();return width;}public synchronized int bridgeHeight(){check();return height;}
 synchronized void resize(int w,int h){width=w;height=h;}
 public synchronized Canvas lockCanvas(Rect dirty){check();if(locked!=null)throw new IllegalStateException("Surface already locked");bitmap=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888);locked=new Canvas(bitmap);return locked;}
 public synchronized void unlockCanvasAndPost(Canvas c){check();if(c!=locked||c==null)throw new IllegalArgumentException("Wrong Canvas");c.bridgeDispose();present(bitmap.bridgeBytes());locked=null;bitmap=null;}
 private void check(){if(!valid||width<=0||height<=0)throw new IllegalStateException("Surface is not available");}
 public synchronized void bridgeRGBA(ByteBuffer rgba,int w,int h){check();if(w<1||h<1||(long)w*h>8388608||rgba.remaining()!=(long)w*h*4)throw new IllegalArgumentException("Invalid RGBA frame");Bitmap b=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);int[] pixels=new int[w*h];for(int i=0;i<pixels.length;i++){int r=rgba.get()&255,g=rgba.get()&255,blue=rgba.get()&255,a=rgba.get()&255;pixels[i]=(a<<24)|(r<<16)|(g<<8)|blue;}b.bridgeImage.setRGB(0,0,w,h,pixels,0,w);present(b.bridgeBytes());}
 private void present(byte[] png){org.padtv.bridge.Native.image(view,png);if(Boolean.getBoolean("padbridge.headless"))try{java.nio.file.Files.write(java.nio.file.Paths.get("/data/surface-"+view+".png"),png);}catch(java.io.IOException e){throw new IllegalStateException(e);}}
}
