package org.padtv.lifecycleprobe;
import android.app.*;import android.os.Bundle;
public class ProbeApplication extends Application {
 public static boolean initialized;
 public void onCreate(){super.onCreate();initialized=true;registerActivityLifecycleCallbacks(new ActivityLifecycleCallbacks(){public void onActivityCreated(Activity a,Bundle b){System.out.println("APP_LIFECYCLE_CREATED");}public void onActivityStarted(Activity a){System.out.println("APP_LIFECYCLE_STARTED");}public void onActivityResumed(Activity a){System.out.println("APP_LIFECYCLE_RESUMED");}public void onActivityPaused(Activity a){System.out.println("APP_LIFECYCLE_PAUSED");}public void onActivityStopped(Activity a){System.out.println("APP_LIFECYCLE_STOPPED");}public void onActivitySaveInstanceState(Activity a,Bundle b){}public void onActivityDestroyed(Activity a){System.out.println("APP_LIFECYCLE_DESTROYED");}});}
}
