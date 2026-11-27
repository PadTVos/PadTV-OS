package org.padtv.artprobe;
import java.lang.reflect.*;import java.util.*;import java.util.concurrent.*;import java.util.concurrent.atomic.*;
/** Compiled once by D8; the same original DEX bytes must be consumed by ART. */
public final class RuntimeProbe {
    private final String text;public RuntimeProbe(String value){text=value;}public String message(){return text;}
    public static void main(String[] args)throws Exception {
        String vm=System.getProperty("java.vm.name");if(!"Dalvik".equals(vm))throw new AssertionError("Expected ART/libcore, got "+vm);
        Class<?> type=Class.forName("org.padtv.artprobe.RuntimeProbe");Object instance=type.getConstructor(String.class).newInstance("ORIGINAL_DEX");
        if(!"ORIGINAL_DEX".equals(type.getMethod("message").invoke(instance)))throw new AssertionError("Reflection");
        final AtomicInteger count=new AtomicInteger();final CountDownLatch ready=new CountDownLatch(4);List<Thread> workers=new ArrayList<Thread>();
        for(int n=0;n<4;n++){Thread thread=new Thread(new Runnable(){public void run(){for(int i=0;i<10000;i++)count.incrementAndGet();ready.countDown();}},"original-dex-worker-"+n);workers.add(thread);thread.start();}
        if(!ready.await(10,TimeUnit.SECONDS))throw new AssertionError("Thread timeout");for(Thread thread:workers)thread.join();if(count.get()!=40000)throw new AssertionError("Atomic execution");
        int exceptions=0;try{throw new IllegalArgumentException("original-exception");}catch(IllegalArgumentException e){if(!e.getMessage().equals("original-exception"))throw e;exceptions++;}
        if(exceptions!=1)throw new AssertionError("Exception flow");
        if(new java.io.File("/home/padtv").exists()||new java.io.File("/tmp/padbridge-host-secret").exists())throw new AssertionError("Host data exposed");
        String output="ART_ORIGINAL_DEX_REFLECTION_THREADS_EXCEPTIONS_OK "+count.get();
        try(java.io.FileOutputStream stream=new java.io.FileOutputStream("/data/art-result.txt")){stream.write(output.getBytes("UTF-8"));}
        System.out.println(output);
    }
}
