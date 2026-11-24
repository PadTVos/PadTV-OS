package android.app;
import android.content.Context;
import android.os.Bundle;
import android.view.View;
import android.view.KeyEvent;
public class Activity extends Context implements android.view.Window.Callback {
    private final android.view.Window window=new android.view.Window(this);
    public Activity(){window.setCallback(this);}
    private boolean started;
    private View content;
    private android.content.Intent intent=new android.content.Intent();
    protected void onCreate(Bundle state) { }
    protected void onStart() { }
    protected void onResume() { }
    protected void onPause() { }
    protected void onStop() { }
    protected void onDestroy() { }
    // Android lifecycle hooks intentionally have empty base implementations:
    // subclasses override them; bridgeStart/Stop actually dispatch the lifecycle.
    public final void bridgeStart() { if(started)throw new IllegalStateException("Already started");started=true;onCreate(null);onStart();onResume();onAttachedToWindow();onWindowFocusChanged(true); }
    public final void bridgeStop() { if(started){onWindowFocusChanged(false);if(content!=null)View.bridgeDetach(content);onDetachedFromWindow();onPause();onStop();onDestroy();started=false;} }
    public void setContentView(View view) { content=view;window.setContentView(view); }
    public void setContentView(int resource) { setContentView(android.view.LayoutInflater.from(this).inflate(resource,null,false)); }
    public View findViewById(int id){return content==null?null:content.findViewById(id);}
    public void runOnUiThread(Runnable r){if(Thread.currentThread()==android.os.Looper.getMainLooper().getThread())r.run();else new android.os.Handler(android.os.Looper.getMainLooper()).post(r);}
    public boolean onKeyDown(int key, KeyEvent event) { return false; }
    public boolean onKeyUp(int key,KeyEvent event){return false;}
    public boolean dispatchKeyEvent(KeyEvent event){return event.getAction()==0?onKeyDown(event.getKeyCode(),event):onKeyUp(event.getKeyCode(),event);}
    public android.view.Window getWindow(){return window;}public android.view.WindowManager getWindowManager(){return new android.view.WindowManager(){public android.view.Display getDefaultDisplay(){return new android.view.Display();}};}
    public boolean requestWindowFeature(int f){return window.requestFeature(f);}public void finishAndRemoveTask(){finish();}
    public void onWindowFocusChanged(boolean focus){}public void onContentChanged(){}public void onWindowAttributesChanged(android.view.WindowManager.LayoutParams p){}public void onAttachedToWindow(){}public void onDetachedFromWindow(){}
    public android.content.Intent getIntent(){return intent;}public void setIntent(android.content.Intent i){intent=i;}
    public void finish(){org.padtv.bridge.Host.finish(this);}public void onBackPressed(){finish();}
    public void bridgePause(){onPause();onStop();}public void bridgeResume(){if(content!=null)org.padtv.bridge.Host.setContent(content);onStart();onResume();}
}
