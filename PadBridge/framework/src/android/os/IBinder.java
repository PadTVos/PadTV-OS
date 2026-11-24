package android.os;
public interface IBinder {
    int FIRST_CALL_TRANSACTION=1,INTERFACE_TRANSACTION=0x5f4e5446,FLAG_ONEWAY=1;
    String getInterfaceDescriptor()throws RemoteException;boolean pingBinder();boolean isBinderAlive();IInterface queryLocalInterface(String descriptor);boolean transact(int code,Parcel data,Parcel reply,int flags)throws RemoteException;
    interface DeathRecipient {void binderDied();}
}
