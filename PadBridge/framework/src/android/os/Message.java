package android.os;
public class Message { public int what,arg1,arg2; public Object obj; Handler target; Runnable callback; long when,sequence; private Bundle data;
    public static Message obtain(){return new Message();}
    public static Message obtain(Handler h,int what){Message m=obtain();m.target=h;m.what=what;return m;}
    public static Message obtain(Handler h,int what,Object obj){Message m=obtain(h,what);m.obj=obj;return m;}
    public Bundle getData(){if(data==null)data=new Bundle();return data;}public void setData(Bundle b){data=b;}
    public void sendToTarget(){target.sendMessage(this);} public Handler getTarget(){return target;}
}
