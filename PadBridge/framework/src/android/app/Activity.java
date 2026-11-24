package android.app;
import android.content.Context;
import android.os.Bundle;
import android.view.View;
import android.view.KeyEvent;
public class Activity extends Context {
    private boolean started;
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
    public void setContentView(View view) { org.padtv.bridge.Host.setContent(view); }
    public void setContentView(int resource) { throw new UnsupportedOperationException("Compiled layout resources are not supported"); }
    public boolean onKeyDown(int key, KeyEvent event) { return false; }
}
