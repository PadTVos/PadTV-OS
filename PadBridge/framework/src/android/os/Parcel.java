package android.os;
import java.nio.*;
public final class Parcel {
    private ByteBuffer bytes=ByteBuffer.allocate(1024).order(ByteOrder.LITTLE_ENDIAN);private int length;
    private void need(int n){if(n<0||bytes.position()+n>1024*1024)throw new IllegalArgumentException("Parcel exceeds 1 MiB");if(bytes.remaining()<n){ByteBuffer next=ByteBuffer.allocate(Math.min(1024*1024,Math.max(bytes.capacity()*2,bytes.position()+n))).order(ByteOrder.LITTLE_ENDIAN);int p=bytes.position();next.put(bytes.array(),0,length);next.position(p);bytes=next;}}
    private void readable(int n){if(n<0||bytes.position()+n>length)throw new IllegalArgumentException("Truncated Parcel");}
    public static Parcel obtain(){return new Parcel();}public void recycle(){bytes.clear();length=0;}
    public int dataPosition(){return bytes.position();}public int dataSize(){return length;}public void setDataPosition(int p){if(p<0||p>length)throw new IllegalArgumentException("Parcel position");bytes.position(p);}
    public void writeInt(int n){need(4);bytes.putInt(n);length=Math.max(length,bytes.position());}public int readInt(){readable(4);return bytes.getInt();}
    public void writeLong(long n){need(8);bytes.putLong(n);length=Math.max(length,bytes.position());}public long readLong(){readable(8);return bytes.getLong();}
    public void writeFloat(float value){writeInt(Float.floatToRawIntBits(value));}public float readFloat(){return Float.intBitsToFloat(readInt());}
    public void writeDouble(double value){writeLong(Double.doubleToRawLongBits(value));}public double readDouble(){return Double.longBitsToDouble(readLong());}
    public void writeString(String s){if(s==null){writeInt(-1);return;}writeInt(s.length());byte[] utf=s.getBytes(java.nio.charset.StandardCharsets.UTF_16LE);int padded=(utf.length+2+3)&~3;need(padded);bytes.put(utf);for(int i=utf.length;i<padded;i++)bytes.put((byte)0);length=Math.max(length,bytes.position());}
    public String readString(){int n=readInt();if(n==-1)return null;if(n<0||n>500000)throw new IllegalArgumentException("Parcel string size");int padded=(n*2+2+3)&~3;readable(padded);String s=new String(bytes.array(),bytes.position(),n*2,java.nio.charset.StandardCharsets.UTF_16LE);bytes.position(bytes.position()+padded);return s;}
    public void writeInterfaceToken(String d){writeInt(0);writeString(d);}public void enforceInterface(String d){readInt();if(!d.equals(readString()))throw new SecurityException("Binder interface token mismatch");}
    public void writeNoException(){writeInt(0);}public void readException(){int code=readInt();if(code!=0)throw new IllegalStateException("Remote exception "+code+": "+readString());}
    public byte[] marshall(){return java.util.Arrays.copyOf(bytes.array(),length);}public void unmarshall(byte[] data,int offset,int count){if(count<0||count>1024*1024)throw new IllegalArgumentException("Parcel size");bytes=ByteBuffer.allocate(Math.max(count,1)).order(ByteOrder.LITTLE_ENDIAN);bytes.put(data,offset,count);length=count;bytes.position(0);}
}
