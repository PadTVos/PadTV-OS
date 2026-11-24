package android.os;
/** Local Binder dispatch only. No kernel Binder or cross-process handles. */
public class Binder implements IBinder {
    private IInterface owner;private String descriptor;
    public void attachInterface(IInterface o,String d){owner=o;descriptor=d;}public String getInterfaceDescriptor(){return descriptor;}public IInterface queryLocalInterface(String d){return d.equals(descriptor)?owner:null;}
    public boolean pingBinder(){return true;}public boolean isBinderAlive(){return true;}
    public final boolean transact(int code,Parcel data,Parcel reply,int flags)throws RemoteException {if(flags!=0)throw new UnsupportedOperationException("Asynchronous/remote Binder transactions unavailable");int p=data.dataPosition();data.setDataPosition(0);try{boolean handled=onTransact(code,data,reply,flags);if(reply!=null)reply.setDataPosition(0);return handled;}finally{data.setDataPosition(p);}}
    protected boolean onTransact(int code,Parcel data,Parcel reply,int flags)throws RemoteException {if(code==INTERFACE_TRANSACTION){reply.writeString(descriptor);return true;}return false;}
    public IBinder asBinder(){return this;}
}
