package android.os;
public final class SystemClock {
    public static long uptimeMillis(){return System.nanoTime()/1000000L;}
    public static long elapsedRealtime(){return uptimeMillis();}
    public static void sleep(long ms){boolean interrupted=false;long end=uptimeMillis()+ms;while(ms>0)try{Thread.sleep(ms);break;}catch(InterruptedException e){interrupted=true;ms=end-uptimeMillis();}if(interrupted)Thread.currentThread().interrupt();}
}
