package android.app;
import android.content.Context;
import android.os.Bundle;
import android.view.View;
import android.view.KeyEvent;
public class Activity extends Context {
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
    public final void bridgeStart() { if(started)throw new IllegalStateException("Already started");started=true;onCreate(null);onStart();onResume(); }
    public final void bridgeStop() { if(started){onPause();onStop();onDestroy();started=false;} }
    public void setContentView(View view) { content=view;org.padtv.bridge.Host.setContent(view); }
    public void setContentView(int resource) { setContentView(android.view.LayoutInflater.from(this).inflate(resource,null,false)); }
    public View findViewById(int id){return content==null?null:content.findViewById(id);}
    public void runOnUiThread(Runnable r){if(Thread.currentThread()==android.os.Looper.getMainLooper().getThread())r.run();else new android.os.Handler(android.os.Looper.getMainLooper()).post(r);}
    public boolean onKeyDown(int key, KeyEvent event) { return false; }
    public android.content.Intent getIntent(){return intent;}public void setIntent(android.content.Intent i){intent=i;}
    public void finish(){org.padtv.bridge.Host.finish(this);}public void onBackPressed(){finish();}
    public void bridgePause(){onPause();onStop();}public void bridgeResume(){if(content!=null)org.padtv.bridge.Host.setContent(content);onStart();onResume();}
}
