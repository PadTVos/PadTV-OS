package android.app;
import java.util.*;
/** Process-local information, not Android's global task manager. */
public class ActivityManager {
    public static class RunningAppProcessInfo {public String processName;public int pid;public String[] pkgList;}
    public int getMemoryClass(){return (int)(Runtime.getRuntime().maxMemory()/(1024*1024));}
    public List<RunningAppProcessInfo> getRunningAppProcesses(){RunningAppProcessInfo i=new RunningAppProcessInfo();i.processName=org.padtv.bridge.Host.packageName;i.pkgList=new String[]{i.processName};i.pid=Integer.parseInt(java.lang.management.ManagementFactory.getRuntimeMXBean().getName().split("@")[0]);return Collections.singletonList(i);}
}
