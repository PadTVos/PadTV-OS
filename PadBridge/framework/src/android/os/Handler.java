package android.os;
public class Handler {
    public interface Callback{boolean handleMessage(Message m);}private final Looper looper;private final Callback callback;
    public Handler(){this(Looper.myLooper(),null);}public Handler(Looper l){this(l,null);}public Handler(Callback c){this(Looper.myLooper(),c);}public Handler(Looper l,Callback c){if(l==null)throw new IllegalStateException("Handler requires a Looper");looper=l;callback=c;}
    public Looper getLooper(){return looper;}public void handleMessage(Message m){}
    public void dispatchMessage(Message m){if(m.callback!=null)m.callback.run();else if(callback==null||!callback.handleMessage(m))handleMessage(m);}
    public boolean post(Runnable r){return postDelayed(r,0);}public boolean postDelayed(Runnable r,long delay){Message m=Message.obtain();m.callback=r;return sendMessageDelayed(m,delay);}
    public boolean sendMessage(Message m){return sendMessageDelayed(m,0);}public boolean sendMessageDelayed(Message m,long delay){return sendMessageAtTime(m,SystemClock.uptimeMillis()+Math.max(0,delay));}
    public boolean sendMessageAtTime(Message m,long when){m.target=this;return looper.enqueue(m,when);}
    public boolean sendEmptyMessage(int what){return sendMessage(obtainMessage(what));}public Message obtainMessage(int what){return Message.obtain(this,what);}public Message obtainMessage(int what,Object obj){return Message.obtain(this,what,obj);}
    public void removeCallbacks(Runnable r){looper.remove(this,r,null,null);}public void removeMessages(int what){looper.remove(this,null,null,what);}public void removeCallbacksAndMessages(Object token){looper.remove(this,null,token,null);}
}
