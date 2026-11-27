package android.app;
import android.content.*;
import android.os.Bundle;
import java.util.*;
public class Application extends ContextWrapper implements ComponentCallbacks2 {
 private final List<ActivityLifecycleCallbacks> lifecycle=new ArrayList<ActivityLifecycleCallbacks>();private final List<ComponentCallbacks> components=new ArrayList<ComponentCallbacks>();
 public Application(){super(null);}public final void bridgeAttach(Context base){attachBaseContext(base);}public void onCreate(){}public void onTerminate(){}
 public Context getApplicationContext(){return this;}
 public interface ActivityLifecycleCallbacks {void onActivityCreated(Activity a,Bundle b);void onActivityStarted(Activity a);void onActivityResumed(Activity a);void onActivityPaused(Activity a);void onActivityStopped(Activity a);void onActivitySaveInstanceState(Activity a,Bundle b);void onActivityDestroyed(Activity a);}
 public void registerActivityLifecycleCallbacks(ActivityLifecycleCallbacks c){if(c==null)throw new NullPointerException();synchronized(lifecycle){if(!lifecycle.contains(c))lifecycle.add(c);}}public void unregisterActivityLifecycleCallbacks(ActivityLifecycleCallbacks c){synchronized(lifecycle){lifecycle.remove(c);}}
 public void bridgeLifecycle(Activity a,int state){List<ActivityLifecycleCallbacks> copy;synchronized(lifecycle){copy=new ArrayList<ActivityLifecycleCallbacks>(lifecycle);}for(ActivityLifecycleCallbacks c:copy)switch(state){case 0:c.onActivityCreated(a,null);break;case 1:c.onActivityStarted(a);break;case 2:c.onActivityResumed(a);break;case 3:c.onActivityPaused(a);break;case 4:c.onActivityStopped(a);break;case 5:c.onActivityDestroyed(a);break;default:throw new IllegalArgumentException();}}
 public void registerComponentCallbacks(ComponentCallbacks c){synchronized(components){if(!components.contains(c))components.add(c);}}public void unregisterComponentCallbacks(ComponentCallbacks c){synchronized(components){components.remove(c);}}
 private List<ComponentCallbacks> callbacks(){synchronized(components){return new ArrayList<ComponentCallbacks>(components);}}
 public void onConfigurationChanged(android.content.res.Configuration c){for(ComponentCallbacks callback:callbacks())callback.onConfigurationChanged(c);}public void onLowMemory(){for(ComponentCallbacks c:callbacks())c.onLowMemory();}public void onTrimMemory(int level){for(ComponentCallbacks c:callbacks())if(c instanceof ComponentCallbacks2)((ComponentCallbacks2)c).onTrimMemory(level);}
}
