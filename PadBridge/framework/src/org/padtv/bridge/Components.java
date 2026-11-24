package org.padtv.bridge;
import android.content.*;
import android.app.Service;
import java.util.*;
public final class Components {
    private static final Map<String,Service> services=new HashMap<String,Service>();private static int starts;
    private static final Map<BroadcastReceiver,Registration> receivers=new LinkedHashMap<BroadcastReceiver,Registration>();
    private static final class Registration {Context context;IntentFilter filter;Registration(Context c,IntentFilter f){context=c;filter=f;}}
    public static String target(Context context,Intent intent){ComponentName c=intent.getComponent();if(c==null||!c.getPackageName().equals(context.getPackageName()))throw new UnsupportedOperationException("Only explicit same-package components are supported");return c.getClassName();}
    public static synchronized ComponentName start(Context context,Intent intent){String name=target(context,intent);Manifest.require("service",name);try{Service s=services.get(name);if(s==null){s=(Service)Class.forName(name).getDeclaredConstructor().newInstance();services.put(name,s);s.onCreate();}s.onStartCommand(intent,0,++starts);return intent.getComponent();}catch(RuntimeException e){throw e;}catch(Exception e){throw new IllegalStateException(e);}}
    public static synchronized boolean stop(String name){Service s=services.remove(name);if(s==null)return false;s.onDestroy();return true;}
    public static synchronized Intent register(Context c,BroadcastReceiver r,IntentFilter filter){if(r==null)return null;receivers.put(r,new Registration(c,filter));return null;}
    public static synchronized void unregister(BroadcastReceiver r){if(receivers.remove(r)==null)throw new IllegalArgumentException("Receiver was not registered");}
    public static void broadcast(final Context c,final Intent i){if(i.getPackage()!=null&&!i.getPackage().equals(c.getPackageName()))throw new SecurityException("Cross-package broadcasts unavailable");final Map<BroadcastReceiver,Registration> copy; synchronized(Components.class){copy=new LinkedHashMap<BroadcastReceiver,Registration>(receivers);}new android.os.Handler(android.os.Looper.getMainLooper()).post(new Runnable(){public void run(){for(Map.Entry<BroadcastReceiver,Registration> e:copy.entrySet())if(e.getValue().filter.hasAction(i.getAction()))e.getKey().onReceive(e.getValue().context,i);}});}
}
