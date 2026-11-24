package org.padtv.runtimeprobe;
import android.app.Activity;
import android.content.*;
import android.os.*;
import android.database.*;
import android.database.sqlite.*;
import android.view.View;
import android.widget.TextView;

/** Compiled against Google's Android API jar, then D8; no PadBridge imports. */
public class RuntimeActivity extends Activity {
    public static String reflected(){return "REFLECTION_OK";}
    private volatile int workerResult;
    public void onCreate(Bundle state){super.onCreate(state);
        try {
            final SharedPreferences prefs=getSharedPreferences("settings",MODE_PRIVATE);
            int count=prefs.getInt("runs",0)+1;
            if(!prefs.edit().putInt("runs",count).putString("text","Český Android").commit())throw new AssertionError("Preferences commit");
            if(!prefs.getString("text","").equals("Český Android"))throw new AssertionError("Preferences Unicode");
            SQLiteDatabase db=openOrCreateDatabase("state.db",MODE_PRIVATE,null);
            db.execSQL("CREATE TABLE IF NOT EXISTS numbers (value INTEGER)");
            db.beginTransaction();db.execSQL("INSERT INTO numbers VALUES (?)",new Object[]{42});db.endTransaction();
            Cursor c=db.rawQuery("SELECT COUNT(*) FROM numbers",null);c.moveToFirst();if(c.getInt(0)!=0)throw new AssertionError("SQLite rollback");c.close();db.close();
            String reflected=(String)getClassLoader().loadClass(getClass().getName()).getMethod("reflected").invoke(null);
            if(!reflected.equals("REFLECTION_OK"))throw new AssertionError("Reflection");
            try{Integer.parseInt("not-a-number");throw new AssertionError("Exception missing");}catch(NumberFormatException expected){}
            HandlerThread worker=new HandlerThread("APK worker");worker.start();
            final java.util.concurrent.CountDownLatch done=new java.util.concurrent.CountDownLatch(1);
            new Handler(worker.getLooper()).post(new Runnable(){public void run(){workerResult=6*7;done.countDown();}});
            if(!done.await(2,java.util.concurrent.TimeUnit.SECONDS)||workerResult!=42)throw new AssertionError("Looper thread");worker.quit();worker.join(2000);
            Binder binder=new Binder(){protected boolean onTransact(int code,Parcel data,Parcel reply,int flags)throws RemoteException{data.enforceInterface("org.padtv.probe");reply.writeNoException();reply.writeInt(data.readInt()*7);return true;}};
            Parcel request=Parcel.obtain(),response=Parcel.obtain();request.writeInterfaceToken("org.padtv.probe");request.writeInt(6);binder.transact(1,request,response,0);response.readException();if(response.readInt()!=42)throw new AssertionError("Local Binder");
            final BroadcastReceiver receiver=new BroadcastReceiver(){public void onReceive(Context context,Intent intent){if(intent.getIntExtra("value",0)!=42)throw new AssertionError("Intent extra");android.util.Log.i("PROBE","BROADCAST_OK");unregisterReceiver(this);}};
            registerReceiver(receiver,new IntentFilter("org.padtv.TEST"));sendBroadcast(new Intent("org.padtv.TEST").putExtra("value",42));
            Intent service=new Intent(this,ProbeService.class).putExtra("value",42);startService(service);if(!stopService(service))throw new AssertionError("Service stop");
            Cursor provider=getContentResolver().query(android.net.Uri.parse("content://org.padtv.probe/value"),null,null,null,null);provider.moveToFirst();if(provider.getInt(0)!=42)throw new AssertionError("Content provider");provider.close();
            android.util.Log.i("PROBE","CONTENT_PROVIDER_OK");
            if(Secondary.answer()!=42)throw new AssertionError("Secondary DEX class");
            setContentView(getResources().getIdentifier("main","layout",getPackageName()));
            final TextView result=(TextView)findViewById(getResources().getIdentifier("result","id",getPackageName()));
            result.setText("Java DEX · XML · SQLite · runs="+count);
            new Handler().postDelayed(new Runnable(){public void run(){result.setText(result.getText()+" · HANDLER_OK");android.util.Log.i("PROBE","HANDLER_OK");}},20);
            android.util.Log.i("PROBE","JAVA_SQLITE_PREFS_THREADS_REFLECTION_BINDER_MULTIDEX_OK");
        }catch(Exception e){throw new RuntimeException(e);}
    }
    public void select(View view){((TextView)view).setText("XML_DPAD_OK");android.util.Log.i("PROBE","XML_DPAD_OK");}
}
