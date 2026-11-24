package org.padtv.runtimeprobe;
public class ProbeService extends android.app.Service {
    public int onStartCommand(android.content.Intent i,int flags,int id){android.util.Log.i("PROBE","SERVICE_STARTED_"+i.getIntExtra("value",0));return START_NOT_STICKY;}
    public android.os.IBinder onBind(android.content.Intent i){return new android.os.Binder();}
    public void onDestroy(){android.util.Log.i("PROBE","SERVICE_STOPPED");}
}
