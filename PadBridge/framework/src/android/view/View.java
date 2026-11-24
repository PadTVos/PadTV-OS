package android.view;
import android.content.Context;
import org.padtv.bridge.Native;
public class View {
    public final int bridgeId;
    protected final Context context;
    private OnClickListener listener;
    public static final int VISIBLE=0,INVISIBLE=4,GONE=8;
    private OnFocusChangeListener focusListener;private boolean focused,focusable,enabled=true,clickable,attached,dirty=true;
    private int width,height,visibility,background,systemUi,padLeft,padTop,padRight,padBottom;
    protected boolean canvasDrawing;
    private final android.os.Handler handler=new android.os.Handler(android.os.Looper.getMainLooper());
    private static final java.util.Map<Integer,View> registry=new java.util.LinkedHashMap<Integer,View>();
    private int id=-1;private ViewGroup.LayoutParams layoutParams=new ViewGroup.LayoutParams(-2,-2);
    public View(Context ctx){this(ctx,0);}
    protected View(Context ctx,int kind){context=ctx;bridgeId=Native.create(kind);registry.put(bridgeId,this);canvasDrawing=kind==0;}
    public View(Context c,android.util.AttributeSet a){this(c);}public View(Context c,android.util.AttributeSet a,int style){this(c,a);}
    public interface OnFocusChangeListener{void onFocusChange(View view,boolean focused);}
    public interface OnClickListener{void onClick(View view);}
    public void setOnClickListener(OnClickListener value){listener=value;}
    public boolean performClick(){if(!enabled||visibility!=VISIBLE||listener==null)return false;listener.onClick(this);return true;}
    public Context getContext(){return context;}
    public void setId(int value){id=value;}public int getId(){return id;}
    public View findViewById(int value){return value==id?this:null;}
    public void setLayoutParams(ViewGroup.LayoutParams p){layoutParams=p;Native.size(bridgeId,p.width,p.height);}public ViewGroup.LayoutParams getLayoutParams(){return layoutParams;}
    public boolean post(Runnable r){return handler.post(r);}public boolean postDelayed(Runnable r,long ms){return handler.postDelayed(r,ms);}
    public boolean removeCallbacks(Runnable r){handler.removeCallbacks(r);return true;}public void postOnAnimation(Runnable r){postDelayed(r,16);}
    public void setFocusable(boolean v){focusable=v;}public boolean isFocusable(){return focusable||this instanceof android.widget.Button;}
    public void setFocusableInTouchMode(boolean v){focusable=v;}public void setClickable(boolean v){clickable=v;}public boolean isClickable(){return clickable||listener!=null;}
    public void setEnabled(boolean v){enabled=v;}public boolean isEnabled(){return enabled;}public void setOnFocusChangeListener(OnFocusChangeListener l){focusListener=l;}
    public void bridgeFocus(boolean v){if(focused==v)return;focused=v;if(focusListener!=null)focusListener.onFocusChange(this,v);invalidate();}
    public boolean requestFocus(){if(!isFocusable()||!enabled||visibility!=VISIBLE)return false;org.padtv.bridge.Host.focusView(this);return true;}
    public boolean hasFocus(){return focused;}public boolean isFocused(){return focused;}
    public void setVisibility(int v){if(v!=0&&v!=4&&v!=8)throw new IllegalArgumentException();visibility=v;Native.visibility(bridgeId,v);invalidate();}public int getVisibility(){return visibility;}
    public void setBackgroundColor(int c){background=c;canvasDrawing=true;invalidate();}
    public void setPadding(int l,int t,int r,int b){padLeft=l;padTop=t;padRight=r;padBottom=b;invalidate();}
    public int getPaddingLeft(){return padLeft;}public int getPaddingTop(){return padTop;}public int getPaddingRight(){return padRight;}public int getPaddingBottom(){return padBottom;}
    public int getWidth(){return width;}public int getHeight(){return height;}public android.content.res.Resources getResources(){return context.getResources();}
    public void setSystemUiVisibility(int flags){systemUi=flags;if((flags&4)!=0)Native.windowFlags(1024);}public int getSystemUiVisibility(){return systemUi;}
    public void invalidate(){dirty=true;}public void postInvalidate(){post(new Runnable(){public void run(){invalidate();}});}public void requestLayout(){invalidate();}
    protected void onDraw(android.graphics.Canvas canvas){}protected void onSizeChanged(int w,int h,int oldw,int oldh){}protected void onLayout(boolean changed,int l,int t,int r,int b){}
    protected void onAttachedToWindow(){}protected void onDetachedFromWindow(){}
    public void draw(android.graphics.Canvas canvas){if(background!=0)canvas.drawColor(background);onDraw(canvas);}
    public static void bridgeDetach(View view){if(view.attached){view.onDetachedFromWindow();view.attached=false;}if(view instanceof ViewGroup)for(View child:((ViewGroup)view).children)bridgeDetach(child);}
    public static View bridgeFind(int id){return registry.get(id);}
    public static void bridgeLayout(int id,int w,int h){View v=registry.get(id);if(v==null)return;if(!v.attached){v.attached=true;v.onAttachedToWindow();}if(v.width!=w||v.height!=h){int ow=v.width,oh=v.height;v.width=w;v.height=h;v.onSizeChanged(w,h,ow,oh);v.onLayout(true,0,0,w,h);v.dirty=true;}}
    public static void bridgeDraw(){for(View v:new java.util.ArrayList<View>(registry.values()))if(v.dirty&&v.visibility==0&&v.width>0&&v.height>0){v.dirty=false;if(!v.canvasDrawing||(v instanceof ViewGroup&&v.background==0))continue;android.graphics.Bitmap b=android.graphics.Bitmap.createBitmap(v.width,v.height,android.graphics.Bitmap.Config.ARGB_8888);android.graphics.Canvas c=new android.graphics.Canvas(b);try{v.draw(c);}finally{c.bridgeDispose();}java.io.ByteArrayOutputStream bytes=new java.io.ByteArrayOutputStream();if(!b.compress(android.graphics.Bitmap.CompressFormat.PNG,100,bytes))throw new IllegalStateException("View rendering failed");Native.image(v.bridgeId,bytes.toByteArray());if(Boolean.getBoolean("padbridge.headless"))try{java.nio.file.Files.write(java.nio.file.Paths.get("/data/rendered-view-"+v.bridgeId+".png"),bytes.toByteArray());}catch(java.io.IOException e){throw new IllegalStateException(e);}}}
}
