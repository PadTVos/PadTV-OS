package android.app;
import android.content.*;
public abstract class Service extends Context {
    public static final int START_STICKY=1,START_NOT_STICKY=2,START_REDELIVER_INTENT=3;
    public void onCreate(){}public void onDestroy(){}public int onStartCommand(Intent intent,int flags,int startId){throw new UnsupportedOperationException("Legacy Service.onStart not implemented");}
    public abstract android.os.IBinder onBind(Intent intent);
    public final void stopSelf(){org.padtv.bridge.Components.stop(getClass().getName());}
}
