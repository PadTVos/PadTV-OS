package android.view;
public class Window {
 public interface Callback {boolean dispatchKeyEvent(KeyEvent e);void onWindowFocusChanged(boolean focus);void onContentChanged();void onWindowAttributesChanged(WindowManager.LayoutParams p);void onAttachedToWindow();void onDetachedFromWindow();}
 private final android.content.Context context;private Callback callback;private View decor;private final WindowManager.LayoutParams attributes=new WindowManager.LayoutParams();
 public Window(android.content.Context c){context=c;decor=new android.widget.FrameLayout(c);}
 public void setCallback(Callback c){callback=c;}public Callback getCallback(){return callback;}
 public View getDecorView(){return decor;}public void setContentView(View v){decor=v;org.padtv.bridge.Host.setContent(v);if(callback!=null)callback.onContentChanged();}
 public View findViewById(int id){return decor.findViewById(id);}
 public void addFlags(int flags){setFlags(flags,flags);}public void clearFlags(int flags){setFlags(0,flags);}
 public void setFlags(int flags,int mask){if((mask&~(1024|128))!=0)throw new UnsupportedOperationException("Unsupported window flags "+mask);attributes.flags=(attributes.flags&~mask)|(flags&mask);org.padtv.bridge.Native.windowFlags(attributes.flags);if(callback!=null)callback.onWindowAttributesChanged(attributes);}
 public WindowManager.LayoutParams getAttributes(){return attributes;}public void setAttributes(WindowManager.LayoutParams p){setFlags(p.flags,1024|128);}
 public android.content.Context getContext(){return context;}
 public boolean requestFeature(int feature){if(feature==1)return true;throw new UnsupportedOperationException("Window feature "+feature);}
}
