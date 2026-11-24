package android.os;
import java.util.*;
public final class Looper {
    private static final ThreadLocal<Looper> local=new ThreadLocal<Looper>();private static Looper main;
    private final Thread thread=Thread.currentThread();private final PriorityQueue<Message> queue=new PriorityQueue<Message>(11,new Comparator<Message>(){public int compare(Message a,Message b){int c=Long.compare(a.when,b.when);return c==0?Long.compare(a.sequence,b.sequence):c;}});
    private boolean quit;private long sequence;
    public static void prepare(){if(local.get()!=null)throw new IllegalStateException("One Looper per thread");local.set(new Looper());}
    public static synchronized void prepareMainLooper(){if(main!=null)throw new IllegalStateException("Main Looper already exists");prepare();main=myLooper();}
    public static Looper myLooper(){return local.get();}public static Looper getMainLooper(){if(main==null)throw new IllegalStateException("No main Looper");return main;}
    public Thread getThread(){return thread;}
    synchronized boolean enqueue(Message m,long when){if(quit)return false;if(queue.size()>=10000)throw new IllegalStateException("Message queue limit");m.when=when;m.sequence=sequence++;queue.add(m);notifyAll();return true;}
    synchronized void remove(Handler h,Runnable r,Object token,Integer what){Iterator<Message> it=queue.iterator();while(it.hasNext()){Message m=it.next();if(m.target==h&&(r==null||m.callback==r)&&(token==null||m.obj==token)&&(what==null||m.what==what))it.remove();}}
    public void bridgePump(){if(Thread.currentThread()!=thread)throw new IllegalStateException("Looper dispatched on wrong thread");for(int i=0;i<1000;i++){Message m;synchronized(this){if(quit||queue.isEmpty()||queue.peek().when>SystemClock.uptimeMillis())return;m=queue.remove();}m.target.dispatchMessage(m);}}
    public static void loop(){Looper l=myLooper();if(l==null)throw new IllegalStateException("Call prepare first");while(true){l.bridgePump();synchronized(l){if(l.quit)return;long wait=l.queue.isEmpty()?1000:Math.max(1,l.queue.peek().when-SystemClock.uptimeMillis());try{l.wait(wait);}catch(InterruptedException e){Thread.currentThread().interrupt();l.quit();}}}}
    public synchronized void quit(){quit=true;queue.clear();notifyAll();}public void quitSafely(){quit();}
}
