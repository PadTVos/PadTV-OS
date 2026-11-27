package android.view;
import java.util.concurrent.CopyOnWriteArrayList;

/** Observes actual PadBridge layout, drawing and focus traversals. */
public final class ViewTreeObserver {
    public interface OnGlobalLayoutListener { void onGlobalLayout(); }
    public interface OnPreDrawListener { boolean onPreDraw(); }
    public interface OnDrawListener { void onDraw(); }
    public interface OnScrollChangedListener {void onScrollChanged();}
    public interface OnTouchModeChangeListener {void onTouchModeChanged(boolean inTouchMode);}
    public interface OnWindowAttachListener {void onWindowAttached();void onWindowDetached();}
    public interface OnGlobalFocusChangeListener { void onGlobalFocusChanged(View oldFocus,View newFocus); }
    public interface OnWindowFocusChangeListener { void onWindowFocusChanged(boolean hasFocus); }
    private boolean alive=true;
    private final CopyOnWriteArrayList<OnGlobalLayoutListener> layout=new CopyOnWriteArrayList<OnGlobalLayoutListener>();
    private final CopyOnWriteArrayList<OnPreDrawListener> preDraw=new CopyOnWriteArrayList<OnPreDrawListener>();
    private final CopyOnWriteArrayList<OnDrawListener> draw=new CopyOnWriteArrayList<OnDrawListener>();
    private final CopyOnWriteArrayList<OnScrollChangedListener> scroll=new CopyOnWriteArrayList<OnScrollChangedListener>();
    private final CopyOnWriteArrayList<OnTouchModeChangeListener> touch=new CopyOnWriteArrayList<OnTouchModeChangeListener>();
    private final CopyOnWriteArrayList<OnWindowAttachListener> attach=new CopyOnWriteArrayList<OnWindowAttachListener>();
    private final CopyOnWriteArrayList<OnGlobalFocusChangeListener> focus=new CopyOnWriteArrayList<OnGlobalFocusChangeListener>();
    private final CopyOnWriteArrayList<OnWindowFocusChangeListener> windowFocus=new CopyOnWriteArrayList<OnWindowFocusChangeListener>();
    private void check(){if(!alive)throw new IllegalStateException("ViewTreeObserver is not alive; obtain the current observer from the View");}
    public boolean isAlive(){return alive;}
    public void addOnGlobalLayoutListener(OnGlobalLayoutListener l){check();if(l==null)throw new NullPointerException();layout.add(l);}
    public void removeOnGlobalLayoutListener(OnGlobalLayoutListener l){check();layout.remove(l);}
    public void removeGlobalOnLayoutListener(OnGlobalLayoutListener l){removeOnGlobalLayoutListener(l);}
    public void addOnPreDrawListener(OnPreDrawListener l){check();if(l==null)throw new NullPointerException();preDraw.add(l);}
    public void removeOnPreDrawListener(OnPreDrawListener l){check();preDraw.remove(l);}
    public void addOnDrawListener(OnDrawListener l){check();if(l==null)throw new NullPointerException();draw.add(l);}
    public void removeOnDrawListener(OnDrawListener l){check();draw.remove(l);}
    public void addOnScrollChangedListener(OnScrollChangedListener l){check();if(l==null)throw new NullPointerException();scroll.add(l);}
    public void removeOnScrollChangedListener(OnScrollChangedListener l){check();scroll.remove(l);}
    public void dispatchOnScrollChanged(){check();for(OnScrollChangedListener l:scroll)l.onScrollChanged();}
    public void addOnTouchModeChangeListener(OnTouchModeChangeListener l){check();if(l==null)throw new NullPointerException();touch.add(l);}
    public void removeOnTouchModeChangeListener(OnTouchModeChangeListener l){check();touch.remove(l);}
    public void dispatchOnTouchModeChanged(boolean value){check();for(OnTouchModeChangeListener l:touch)l.onTouchModeChanged(value);}
    public void addOnWindowAttachListener(OnWindowAttachListener l){check();if(l==null)throw new NullPointerException();attach.add(l);}
    public void removeOnWindowAttachListener(OnWindowAttachListener l){check();attach.remove(l);}
    public void bridgeAttached(boolean value){check();for(OnWindowAttachListener l:attach){if(value)l.onWindowAttached();else l.onWindowDetached();}}
    public void addOnGlobalFocusChangeListener(OnGlobalFocusChangeListener l){check();if(l==null)throw new NullPointerException();focus.add(l);}
    public void removeOnGlobalFocusChangeListener(OnGlobalFocusChangeListener l){check();focus.remove(l);}
    public void addOnWindowFocusChangeListener(OnWindowFocusChangeListener l){check();if(l==null)throw new NullPointerException();windowFocus.add(l);}
    public void removeOnWindowFocusChangeListener(OnWindowFocusChangeListener l){check();windowFocus.remove(l);}
    public void dispatchOnGlobalLayout(){check();for(OnGlobalLayoutListener l:layout)l.onGlobalLayout();}
    public boolean dispatchOnPreDraw(){check();boolean cancel=false;for(OnPreDrawListener l:preDraw)cancel|=!l.onPreDraw();return cancel;}
    public void dispatchOnDraw(){check();for(OnDrawListener l:draw)l.onDraw();}
    public void bridgeFocus(View oldView,View newView){check();for(OnGlobalFocusChangeListener l:focus)l.onGlobalFocusChanged(oldView,newView);}
    public void bridgeWindowFocus(boolean value){check();for(OnWindowFocusChangeListener l:windowFocus)l.onWindowFocusChanged(value);}
    void merge(ViewTreeObserver old){if(old==this)return;check();old.check();layout.addAll(old.layout);preDraw.addAll(old.preDraw);draw.addAll(old.draw);scroll.addAll(old.scroll);touch.addAll(old.touch);attach.addAll(old.attach);focus.addAll(old.focus);windowFocus.addAll(old.windowFocus);old.alive=false;old.layout.clear();old.preDraw.clear();old.draw.clear();old.scroll.clear();old.touch.clear();old.attach.clear();old.focus.clear();old.windowFocus.clear();}
}
