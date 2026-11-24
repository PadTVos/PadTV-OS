package org.padtv.bridge;
import android.content.SharedPreferences;
import java.io.*;
import java.nio.file.*;
import java.util.*;
public final class Preferences implements SharedPreferences {
    private static final Map<String,Preferences> instances=new HashMap<String,Preferences>();
    public static synchronized Preferences open(String name) {
        if(!name.matches("[A-Za-z0-9_.-]{1,160}")||name.contains(".."))throw new IllegalArgumentException("Unsafe preference name");
        Preferences p=instances.get(name);if(p==null){p=new Preferences(name);instances.put(name,p);}return p;
    }
    private final File file; private final Properties data=new Properties();
    private final Set<OnSharedPreferenceChangeListener> listeners=new HashSet<OnSharedPreferenceChangeListener>();
    private Preferences(String name){file=new File("/data/shared_prefs",name+".properties");if(file.exists())try(Reader r=new InputStreamReader(new FileInputStream(file),"UTF-8")){data.load(r);}catch(IOException e){throw new IllegalStateException(e);}}
    private synchronized String read(String key,String type){String v=data.getProperty(key);if(v==null)return null;if(!v.startsWith(type+":"))throw new ClassCastException(key);return v.substring(2);}
    public String getString(String k,String d){String v=read(k,"s");return v==null?d:v;}
    public int getInt(String k,int d){String v=read(k,"i");return v==null?d:Integer.parseInt(v);}
    public long getLong(String k,long d){String v=read(k,"l");return v==null?d:Long.parseLong(v);}
    public float getFloat(String k,float d){String v=read(k,"f");return v==null?d:Float.parseFloat(v);}
    public boolean getBoolean(String k,boolean d){String v=read(k,"b");return v==null?d:Boolean.parseBoolean(v);}
    public Set<String> getStringSet(String k,Set<String> d){String v=read(k,"t");if(v==null)return d;Set<String> s=new HashSet<String>();if(!v.isEmpty())for(String x:v.split(",",-1))s.add(new String(Base64.getDecoder().decode(x),java.nio.charset.StandardCharsets.UTF_8));return s;}
    public synchronized boolean contains(String k){return data.containsKey(k);}
    public synchronized Map<String,?> getAll(){Map<String,Object> result=new HashMap<String,Object>();for(String k:data.stringPropertyNames()){String v=data.getProperty(k);switch(v.charAt(0)){case 'i':result.put(k,getInt(k,0));break;case 'l':result.put(k,getLong(k,0));break;case 'f':result.put(k,getFloat(k,0));break;case 'b':result.put(k,getBoolean(k,false));break;case 't':result.put(k,getStringSet(k,null));break;default:result.put(k,getString(k,null));}}return result;}
    public synchronized void registerOnSharedPreferenceChangeListener(OnSharedPreferenceChangeListener l){listeners.add(l);}
    public synchronized void unregisterOnSharedPreferenceChangeListener(OnSharedPreferenceChangeListener l){listeners.remove(l);}
    public Editor edit(){return new Edit();}
    private final class Edit implements Editor {
        private final Map<String,String> changed=new HashMap<String,String>();private boolean clear;
        private Editor put(String k,String t,Object v){changed.put(k,v==null?null:t+":"+v);return this;}
        public Editor putString(String k,String v){return put(k,"s",v);} public Editor putInt(String k,int v){return put(k,"i",v);} public Editor putLong(String k,long v){return put(k,"l",v);} public Editor putFloat(String k,float v){return put(k,"f",v);} public Editor putBoolean(String k,boolean v){return put(k,"b",v);}
        public Editor putStringSet(String k,Set<String> v){if(v==null)return remove(k);List<String> parts=new ArrayList<String>();for(String x:v)parts.add(Base64.getEncoder().encodeToString(x.getBytes(java.nio.charset.StandardCharsets.UTF_8)));return put(k,"t",String.join(",",parts));}
        public Editor remove(String k){changed.put(k,null);return this;} public Editor clear(){clear=true;return this;}
        public boolean commit(){Set<String> keys=new HashSet<String>();List<OnSharedPreferenceChangeListener> notify;
            synchronized(Preferences.this){Properties next=new Properties();if(clear)keys.addAll(data.stringPropertyNames());else next.putAll(data);keys.addAll(changed.keySet());for(Map.Entry<String,String> e:changed.entrySet()){if(e.getValue()==null)next.remove(e.getKey());else next.setProperty(e.getKey(),e.getValue());}
                try{Files.createDirectories(file.toPath().getParent());Path temp=Files.createTempFile(file.toPath().getParent(),"prefs",null);try{try(Writer out=new OutputStreamWriter(new FileOutputStream(temp.toFile()),"UTF-8")){next.store(out,"PadBridge private preferences");}Files.move(temp,file.toPath(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);}finally{Files.deleteIfExists(temp);}}catch(IOException e){return false;}
                data.clear();data.putAll(next);notify=new ArrayList<OnSharedPreferenceChangeListener>(listeners);}
            for(final String k:keys)for(final OnSharedPreferenceChangeListener l:notify)new android.os.Handler(android.os.Looper.getMainLooper()).post(new Runnable(){public void run(){l.onSharedPreferenceChanged(Preferences.this,k);}});return true;
        }
        public void apply(){if(!commit())throw new IllegalStateException("Preference persistence failed");}
    }
}
