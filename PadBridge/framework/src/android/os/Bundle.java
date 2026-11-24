package android.os;
import java.util.HashMap;
public class Bundle {
    private final HashMap<String,Object> values=new HashMap<String,Object>();
    public void putString(String key,String value){values.put(key,value);}
    public String getString(String key){return (String)values.get(key);}
    public void putInt(String key,int value){values.put(key,value);}
    public int getInt(String key){Object v=values.get(key);return v==null?0:(Integer)v;}
    public boolean containsKey(String key){return values.containsKey(key);}
}
