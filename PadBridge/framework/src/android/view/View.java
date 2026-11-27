package android.view;
import android.content.Context;
import org.padtv.bridge.Native;
public class View {
    public final int bridgeId;
    protected final Context context;
    private OnClickListener listener;
    public interface OnCreateContextMenuListener {void onCreateContextMenu(ContextMenu menu,View view,ContextMenu.ContextMenuInfo info);}
    private OnCreateContextMenuListener contextMenuListener;
    public void setOnCreateContextMenuListener(OnCreateContextMenuListener value){contextMenuListener=value;}
    protected void onCreateContextMenu(ContextMenu menu){}
    protected ContextMenu.ContextMenuInfo getContextMenuInfo(){return null;}
    public void createContextMenu(ContextMenu menu){onCreateContextMenu(menu);if(contextMenuListener!=null)contextMenuListener.onCreateContextMenu(menu,this,getContextMenuInfo());}
    public boolean showContextMenu(){return org.padtv.bridge.Host.showContextMenu(this);}
    public static final int VISIBLE=0,INVISIBLE=4,GONE=8;
    private OnFocusChangeListener focusListener;private boolean focused,focusable,enabled=true,clickable,attached,dirty=true;
    private int width,height,visibility,background,systemUi,padLeft,padTop,padRight,padBottom;
    protected boolean canvasDrawing;
    private final android.os.Handler handler=new android.os.Handler(android.os.Looper.getMainLooper());
    private static final java.util.Map<Integer,View> registry=new java.util.LinkedHashMap<Integer,View>();
    private int id=-1;private ViewGroup.LayoutParams layoutParams=new ViewGroup.LayoutParams(-2,-2);
    private ViewGroup parent;
    private ViewTreeObserver observer=new ViewTreeObserver();
    private int left,top,layoutDirection;
    int absoluteX,absoluteY;
    private boolean layoutRequested=true;
    public interface OnAttachStateChangeListener {void onViewAttachedToWindow(View view);void onViewDetachedFromWindow(View view);}
    private final java.util.concurrent.CopyOnWriteArrayList<OnAttachStateChangeListener> attachListeners=new java.util.concurrent.CopyOnWriteArrayList<OnAttachStateChangeListener>();
    public void addOnAttachStateChangeListener(OnAttachStateChangeListener l){if(l==null)throw new NullPointerException();attachListeners.add(l);}
    public void removeOnAttachStateChangeListener(OnAttachStateChangeListener l){attachListeners.remove(l);}
    public boolean isInTouchMode(){return org.padtv.bridge.Host.isInTouchMode();}
    private int scrollX,scrollY;private boolean scrollChanged;
    public interface OnScrollChangeListener {void onScrollChange(View view,int x,int y,int oldX,int oldY);}
    private OnScrollChangeListener scrollListener;
    public void setOnScrollChangeListener(OnScrollChangeListener l){scrollListener=l;}
    public int getScrollX(){return scrollX;}public int getScrollY(){return scrollY;}
    public void scrollTo(int x,int y){if(x==scrollX&&y==scrollY)return;Native.scroll(bridgeId,x,y);int oldX=scrollX,oldY=scrollY;scrollX=x;scrollY=y;scrollChanged=true;onScrollChanged(x,y,oldX,oldY);if(scrollListener!=null)scrollListener.onScrollChange(this,x,y,oldX,oldY);invalidate();}
    public void scrollBy(int x,int y){scrollTo(Math.addExact(scrollX,x),Math.addExact(scrollY,y));}
    protected void onScrollChanged(int x,int y,int oldX,int oldY){}
    private static boolean layoutChanged;
    public interface OnLayoutChangeListener {void onLayoutChange(View v,int left,int top,int right,int bottom,int oldLeft,int oldTop,int oldRight,int oldBottom);}
    private final java.util.concurrent.CopyOnWriteArrayList<OnLayoutChangeListener> layoutListeners=new java.util.concurrent.CopyOnWriteArrayList<OnLayoutChangeListener>();
    public void addOnLayoutChangeListener(OnLayoutChangeListener l){if(l==null)throw new NullPointerException();layoutListeners.add(l);}
    public void removeOnLayoutChangeListener(OnLayoutChangeListener l){layoutListeners.remove(l);}
    public ViewTreeObserver getViewTreeObserver(){return parent==null?observer:parent.getViewTreeObserver();}
    public ViewParent getParent(){return parent;}
    public View getRootView(){return parent==null?this:parent.getRootView();}
    void bridgeParent(ViewGroup p){if(parent!=null)throw new IllegalStateException("View already has a parent");p.getViewTreeObserver().merge(observer);parent=p;requestLayout();}
    public boolean isAttachedToWindow(){return attached;}public boolean isLaidOut(){return width>0&&height>0;}public boolean isLayoutRequested(){return layoutRequested;}
    public int getLeft(){return left;}public int getTop(){return top;}public int getRight(){return left+width;}public int getBottom(){return top+height;}
    public void getLocationOnScreen(int[] out){if(out.length<2)throw new IllegalArgumentException();out[0]=absoluteX;out[1]=absoluteY;}
    public void getLocationInWindow(int[] out){getLocationOnScreen(out);}
    public void setLayoutDirection(int d){if(d!=0&&d!=1)throw new UnsupportedOperationException("Only explicit LTR/RTL direction is supported");layoutDirection=d;setLayoutParams(layoutParams);}
    public int getLayoutDirection(){return layoutDirection;}
    public View(Context ctx){this(ctx,0);}
    protected View(Context ctx,int kind){context=ctx;bridgeId=Native.create(kind);registry.put(bridgeId,this);canvasDrawing=kind==0;}
    public View(Context c,android.util.AttributeSet a){this(c);}public View(Context c,android.util.AttributeSet a,int style){this(c,a);}
    public interface OnFocusChangeListener{void onFocusChange(View view,boolean focused);}
    public interface OnClickListener{void onClick(View view);}
    public void setOnClickListener(OnClickListener value){listener=value;}
    public boolean performClick(){if(!enabled||visibility!=VISIBLE||listener==null)return false;listener.onClick(this);return true;}
    public interface OnKeyListener {boolean onKey(View view,int keyCode,KeyEvent event);}
    private OnKeyListener keyListener;
    public void setOnKeyListener(OnKeyListener listener){keyListener=listener;}
    public boolean onKeyDown(int key,KeyEvent event){return false;}public boolean onKeyUp(int key,KeyEvent event){return false;}
    public boolean dispatchKeyEvent(KeyEvent event){if(enabled&&keyListener!=null&&keyListener.onKey(this,event.getKeyCode(),event))return true;return event.getAction()==KeyEvent.ACTION_DOWN?onKeyDown(event.getKeyCode(),event):onKeyUp(event.getKeyCode(),event);}
    public Context getContext(){return context;}
    public void setId(int value){id=value;}public int getId(){return id;}
    public View findViewById(int value){return value==id?this:null;}
    public void setLayoutParams(ViewGroup.LayoutParams p){if(p==null)throw new NullPointerException();layoutParams=p;Native.size(bridgeId,p.width,p.height);if(p instanceof ViewGroup.MarginLayoutParams){ViewGroup.MarginLayoutParams m=(ViewGroup.MarginLayoutParams)p;m.resolveLayoutDirection(layoutDirection);Native.insets(bridgeId,false,m.leftMargin,m.topMargin,m.rightMargin,m.bottomMargin);}else Native.insets(bridgeId,false,0,0,0,0);requestLayout();}public ViewGroup.LayoutParams getLayoutParams(){return layoutParams;}
    public boolean post(Runnable r){return handler.post(r);}public boolean postDelayed(Runnable r,long ms){return handler.postDelayed(r,ms);}
    public boolean removeCallbacks(Runnable r){handler.removeCallbacks(r);return true;}public void postOnAnimation(Runnable r){postDelayed(r,16);}
    public void setFocusable(boolean v){focusable=v;}public boolean isFocusable(){return focusable||this instanceof android.widget.Button;}
    public void setFocusableInTouchMode(boolean v){focusable=v;}public void setClickable(boolean v){clickable=v;}public boolean isClickable(){return clickable||listener!=null;}
    public void setEnabled(boolean v){enabled=v;}public boolean isEnabled(){return enabled;}public void setOnFocusChangeListener(OnFocusChangeListener l){focusListener=l;}
    public void bridgeFocus(boolean v){if(focused==v)return;focused=v;if(focusListener!=null)focusListener.onFocusChange(this,v);invalidate();}
    public boolean requestFocus(){if(!isFocusable()||!enabled||visibility!=VISIBLE)return false;org.padtv.bridge.Host.focusView(this);return true;}
    public boolean hasFocus(){return focused;}public boolean isFocused(){return focused;}
    public void setVisibility(int v){if(v!=0&&v!=4&&v!=8)throw new IllegalArgumentException();if(visibility==v)return;visibility=v;Native.visibility(bridgeId,v);requestLayout();layoutChanged=true;}public int getVisibility(){return visibility;}
    public void setBackgroundColor(int c){background=c;canvasDrawing=true;invalidate();}
    public void setPadding(int l,int t,int r,int b){padLeft=Math.max(0,l);padTop=Math.max(0,t);padRight=Math.max(0,r);padBottom=Math.max(0,b);Native.insets(bridgeId,true,padLeft,padTop,padRight,padBottom);requestLayout();}
    public int getPaddingLeft(){return padLeft;}public int getPaddingTop(){return padTop;}public int getPaddingRight(){return padRight;}public int getPaddingBottom(){return padBottom;}
    public int getWidth(){return width;}public int getHeight(){return height;}public android.content.res.Resources getResources(){return context.getResources();}
    public void setSystemUiVisibility(int flags){systemUi=flags;if((flags&4)!=0)Native.windowFlags(1024);}public int getSystemUiVisibility(){return systemUi;}
    public void invalidate(){dirty=true;}public void postInvalidate(){post(new Runnable(){public void run(){invalidate();}});}public void requestLayout(){layoutRequested=true;invalidate();if(parent!=null)parent.requestLayout();}
    protected void onDraw(android.graphics.Canvas canvas){}protected void onSizeChanged(int w,int h,int oldw,int oldh){}protected void onLayout(boolean changed,int l,int t,int r,int b){}
    protected void onAttachedToWindow(){}protected void onDetachedFromWindow(){}
    public void draw(android.graphics.Canvas canvas){if(background!=0)canvas.drawColor(background);int save=canvas.save();try{canvas.translate(-scrollX,-scrollY);onDraw(canvas);}finally{canvas.restoreToCount(save);}}
    public static void bridgeDetach(View view){if(view.attached){view.onDetachedFromWindow();view.attached=false;for(OnAttachStateChangeListener l:view.attachListeners)l.onViewDetachedFromWindow(view);if(view.parent==null)view.getViewTreeObserver().bridgeAttached(false);}if(view instanceof ViewGroup)for(View child:((ViewGroup)view).children)bridgeDetach(child);}
    public static View bridgeFind(int id){return registry.get(id);}
    public static void bridgeLayout(int id,int x,int y,int w,int h){View v=registry.get(id);if(v==null)return;if(!v.attached){v.attached=true;v.onAttachedToWindow();for(OnAttachStateChangeListener listener:v.attachListeners)listener.onViewAttachedToWindow(v);if(v.parent==null)v.getViewTreeObserver().bridgeAttached(true);}int l=x-(v.parent==null?0:v.parent.absoluteX-((View)v.parent).scrollX),t=y-(v.parent==null?0:v.parent.absoluteY-((View)v.parent).scrollY);v.absoluteX=x;v.absoluteY=y;boolean changed=v.width!=w||v.height!=h||v.left!=l||v.top!=t;if(changed||v.layoutRequested){int ow=v.width,oh=v.height,ol=v.left,ot=v.top;v.layoutRequested=false;v.width=w;v.height=h;v.left=l;v.top=t;v.absoluteX=x;v.absoluteY=y;if(ow!=w||oh!=h)v.onSizeChanged(w,h,ow,oh);v.onLayout(changed,l,t,l+w,t+h);if(changed)for(OnLayoutChangeListener listener:v.layoutListeners)listener.onLayoutChange(v,l,t,l+w,t+h,ol,ot,ol+ow,ot+oh);v.dirty=true;layoutChanged=true;}}
    public static void bridgeEndLayout(View root){if(root==null)return;if(layoutChanged){layoutChanged=false;root.getViewTreeObserver().dispatchOnGlobalLayout();}boolean scrolled=false;for(View v:registry.values())if(v.scrollChanged&&v.getRootView()==root){v.scrollChanged=false;scrolled=true;}if(scrolled)root.getViewTreeObserver().dispatchOnScrollChanged();}
    public static void bridgeDraw(){for(View v:new java.util.ArrayList<View>(registry.values()))if(v.dirty&&v.visibility==0&&v.width>0&&v.height>0){v.dirty=false;if(!v.canvasDrawing||(v instanceof ViewGroup&&v.background==0))continue;android.graphics.Bitmap b=android.graphics.Bitmap.createBitmap(v.width,v.height,android.graphics.Bitmap.Config.ARGB_8888);android.graphics.Canvas c=new android.graphics.Canvas(b);try{v.draw(c);}finally{c.bridgeDispose();}java.io.ByteArrayOutputStream bytes=new java.io.ByteArrayOutputStream();if(!b.compress(android.graphics.Bitmap.CompressFormat.PNG,100,bytes))throw new IllegalStateException("View rendering failed");Native.image(v.bridgeId,bytes.toByteArray());if(Boolean.getBoolean("padbridge.headless"))try{java.nio.file.Files.write(java.nio.file.Paths.get("/data/rendered-view-"+v.bridgeId+".png"),bytes.toByteArray());}catch(java.io.IOException e){throw new IllegalStateException(e);}}}
}
