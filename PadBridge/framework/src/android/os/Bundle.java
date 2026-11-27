package android.os;
public class Bundle extends BaseBundle implements Cloneable {
    public static final Bundle EMPTY=new Bundle(java.util.Collections.<String,Object>emptyMap());
    private ClassLoader loader;
    public Bundle(){super();}public Bundle(int capacity){super(capacity);}public Bundle(ClassLoader value){this();loader=value;}public Bundle(Bundle other){super(other);loader=other.loader;}
    private Bundle(java.util.Map<String,Object> values){super(values);}
    public Object clone(){return new Bundle(this);}public void putAll(Bundle other){values.putAll(other.values);}
    public void setClassLoader(ClassLoader value){loader=value;}public ClassLoader getClassLoader(){return loader==null?getClass().getClassLoader():loader;}
    public void putBundle(String key,Bundle value){values.put(key,value);}public Bundle getBundle(String key){Object value=values.get(key);return value instanceof Bundle?(Bundle)value:null;}
    public void putFloat(String key,float value){values.put(key,value);}public float getFloat(String key){return getFloat(key,0);}public float getFloat(String key,float fallback){Object value=values.get(key);return value instanceof Float?(Float)value:fallback;}
    public void putByteArray(String key,byte[] value){values.put(key,value);}public byte[] getByteArray(String key){Object value=values.get(key);return value instanceof byte[]?(byte[])value:null;}
    public void putCharSequence(String key,CharSequence value){values.put(key,value);}public CharSequence getCharSequence(String key){return getCharSequence(key,null);}public CharSequence getCharSequence(String key,CharSequence fallback){Object value=values.get(key);return value instanceof CharSequence?(CharSequence)value:fallback;}
    public void putSerializable(String key,java.io.Serializable value){values.put(key,value);}public java.io.Serializable getSerializable(String key){Object value=values.get(key);return value instanceof java.io.Serializable?(java.io.Serializable)value:null;}
}
