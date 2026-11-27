package android.os;
import java.io.*;import java.util.*;

/** Optional per-application tracing to private storage; no host tracefs access. */
public final class Trace {
    public static final long TRACE_TAG_APP=1L<<12;
    private static final ThreadLocal<ArrayDeque<String>> sections=new ThreadLocal<ArrayDeque<String>>(){protected ArrayDeque<String> initialValue(){return new ArrayDeque<String>();}};
    private static final Set<String> asynchronous=new HashSet<String>();
    private Trace() {}
    public static boolean isEnabled(){return Boolean.getBoolean("padbridge.trace");}
    public static boolean isTagEnabled(long tag){return (tag&TRACE_TAG_APP)!=0&&isEnabled();}
    private static String name(String value){if(value==null)throw new NullPointerException();if(value.length()>127)throw new IllegalArgumentException("Trace name exceeds 127 characters");return value;}
    private static synchronized void record(String phase,String title,long value){
        File file=new File("/data/trace.jsonl");if(file.length()>=4*1024*1024)return;
        try(FileOutputStream stream=new FileOutputStream(file,true)){
            String encoded=Base64.getEncoder().encodeToString(title.getBytes("UTF-8"));
            String line="{\"phase\":\""+phase+"\",\"name_base64\":\""+encoded+"\",\"thread\":"+Thread.currentThread().getId()+",\"monotonic_ns\":"+System.nanoTime()+",\"value\":"+value+"}\n";
            stream.write(line.getBytes("UTF-8"));
        }catch(IOException error){throw new IllegalStateException("Private trace output failed",error);}
    }
    public static void beginSection(String title){if(!isEnabled())return;title=name(title);ArrayDeque<String> stack=sections.get();if(stack.size()>=256)throw new IllegalStateException("Trace nesting limit");stack.push(title);record("B",title,0);}
    public static void endSection(){if(!isEnabled())return;ArrayDeque<String> stack=sections.get();if(stack.isEmpty())throw new IllegalStateException("Unbalanced trace section");record("E",stack.pop(),0);}
    public static synchronized void beginAsyncSection(String title,int cookie){if(!isEnabled())return;title=name(title);String key=title+"\0"+cookie;if(asynchronous.size()>=4096||!asynchronous.add(key))throw new IllegalStateException("Duplicate or excessive async trace");record("S",title,cookie);}
    public static synchronized void endAsyncSection(String title,int cookie){if(!isEnabled())return;title=name(title);if(!asynchronous.remove(title+"\0"+cookie))throw new IllegalStateException("Missing async trace");record("F",title,cookie);}
    public static void setCounter(String title,long value){if(isEnabled())record("C",name(title),value);}
    public static void traceBegin(long tag,String title){if(isTagEnabled(tag))beginSection(title);}public static void traceEnd(long tag){if(isTagEnabled(tag))endSection();}
    public static void traceCounter(long tag,String title,int value){if(isTagEnabled(tag))setCounter(title,value);}
}
