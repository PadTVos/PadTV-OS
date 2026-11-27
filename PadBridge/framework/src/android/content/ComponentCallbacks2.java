package android.content;
public interface ComponentCallbacks2 extends ComponentCallbacks {int TRIM_MEMORY_UI_HIDDEN=20,TRIM_MEMORY_RUNNING_LOW=10,TRIM_MEMORY_COMPLETE=80;void onTrimMemory(int level);}
