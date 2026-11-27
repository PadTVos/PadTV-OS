package android.os;
import java.util.*;
/** In-process typed values. Parcel/Binder serialization is a separate contract. */
public class BaseBundle {
    protected final Map<String,Object> values;
    protected BaseBundle(){values=new HashMap<String,Object>();}
    protected BaseBundle(int capacity){values=new HashMap<String,Object>(capacity);}
    protected BaseBundle(BaseBundle other){values=new HashMap<String,Object>(other.values);}
    protected BaseBundle(Map<String,Object> map){values=map;}
    private <T>T value(String key,Class<T> type,T fallback){Object value=values.get(key);return type.isInstance(value)?type.cast(value):fallback;}
    public int size(){return values.size();}public boolean isEmpty(){return values.isEmpty();}public void clear(){values.clear();}public void remove(String key){values.remove(key);}public boolean containsKey(String key){return values.containsKey(key);}public Set<String> keySet(){return values.keySet();}public Object get(String key){return values.get(key);}
    public void putString(String key,String value){values.put(key,value);}public String getString(String key){return getString(key,null);}public String getString(String key,String fallback){return value(key,String.class,fallback);}
    public void putInt(String key,int value){values.put(key,value);}public int getInt(String key){return getInt(key,0);}public int getInt(String key,int fallback){return value(key,Integer.class,fallback);}
    public void putLong(String key,long value){values.put(key,value);}public long getLong(String key){return getLong(key,0);}public long getLong(String key,long fallback){return value(key,Long.class,fallback);}
    public void putBoolean(String key,boolean value){values.put(key,value);}public boolean getBoolean(String key){return getBoolean(key,false);}public boolean getBoolean(String key,boolean fallback){return value(key,Boolean.class,fallback);}
    public void putDouble(String key,double value){values.put(key,value);}public double getDouble(String key){return getDouble(key,0);}public double getDouble(String key,double fallback){return value(key,Double.class,fallback);}
    public void putStringArray(String key,String[] value){values.put(key,value);}public String[] getStringArray(String key){return value(key,String[].class,null);}
    public void putIntArray(String key,int[] value){values.put(key,value);}public int[] getIntArray(String key){return value(key,int[].class,null);}
    public void putLongArray(String key,long[] value){values.put(key,value);}public long[] getLongArray(String key){return value(key,long[].class,null);}
    public void putDoubleArray(String key,double[] value){values.put(key,value);}public double[] getDoubleArray(String key){return value(key,double[].class,null);}
    public void putBooleanArray(String key,boolean[] value){values.put(key,value);}public boolean[] getBooleanArray(String key){return value(key,boolean[].class,null);}
}
